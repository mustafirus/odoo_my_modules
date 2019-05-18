import io
import json
import re
import uuid

from odoo.exceptions import UserError


class TableDict(dict):

    def add_recs(self, newrecs):
        if not newrecs: return
        try:
            self[newrecs._name].add_records(newrecs)
        except KeyError:
            export = not re.match(r"res\.|ir\.|base|report\.|mail\.|omixtory\.host\.template", newrecs._name)
            self[newrecs._name] = Table(newrecs, export)

    def dirty(self):
        return any([v.dirty for v in self.values()])


class Field:
    def __init__(self, table, name, attrs):
        self.table = table
        self.name = name
        self.type = attrs['type']
        self.relation = attrs['relation'] if 'relation' in attrs else None

    def to_json(self, val):
        if self.name == 'id':
            return self.table.xids[(self.table.name, val)]
        if self.type in ["datetime", "date"]:
            return val.timestamp()
        if self.type in ["many2one"]:
            return self.table.xids[(self.relation, val)] if val else None
        if self.type == 'reference':
            if not val:
                return val
            model, id = val.split(',',1)
            return self.table.xids[(model, int(id))]
        return val


class Table:
    def __init__(self, recs, export):
        self.toexport = export
        self.dirty = export
        self.recs = recs
        self.name = recs._name
        self.fields = []
        fg = recs.fields_get()
        self.fields.append(Field(self, 'id', fg['id']))
        del fg['id']
        for name, attrs in fg.items():
            if self._check_field(attrs):
                self.fields.append(Field(self, name, attrs))

    def _check_field(self, attrs):
        return \
            attrs.get('exportable', True) and \
            attrs.get('store', False)

    def add_records(self, new):
        if not new: return
        diff = new - self.recs
        if diff:
            new = self.recs | new
            self.recs = new
            self.dirty = self.toexport

    def get_xids(self):
        xids = ensure_xml_id(self.recs)
        # xids = self.recs.env['ir.model.data'].search([('model', '=', self.name), ('res_id', 'in', self.recs.ids)])
        res = {(self.name, r.id): xid for r,xid in xids}
        # for xid in xids:
        #     res.update({
        #         (xid.model, xid.res_id): xid.complete_name
        #     })
        return res

    def set_xids(self, xids):
        self.xids = xids

    def export(self):
        # [v for v in self.fields if v.type not in ['one2many', 'many2many'] ]
        # [v.name for v in self.fields if v.type not in ['one2many', 'many2many'] ]
        expfields = list(filter(lambda v: v.type not in ['one2many', 'many2many'], self.fields))
        field_list = list(map(lambda v: v.name, expfields))
        query = "SELECT {} from {} where id in %s".format(','.join(field_list), self.recs._table)
        cr = self.recs.env.cr
        cr.execute(query, (tuple(self.recs.ids),), True)
        rows = []
        fetched = cr.fetchall()
        for row in fetched:
            rows.append([expfields[i].to_json(row[i]) for i in range(0, len(expfields))])

        return { 'fields': field_list, 'rows': rows }


class ExportLump:
    def __init__(self, recs):
        self.tables = TableDict()
        self.tables.add_recs(recs)
        self.xids = {}
        while self.tables.dirty():
            for table in list(self.tables.values()):
                self.scan_fields(table)
        for table in self.tables.values():
            self.xids.update(table.get_xids())
            table.xids = self.xids



    def scan_fields(self, table):
        if not (table.toexport and table.dirty): return
        for field in table.fields:
            if field.type in ['many2one', 'many2many', 'one2many']:
                newrecs = table.recs.mapped(field.name)
                self.tables.add_recs(newrecs)
            elif field.type == 'reference':
                for rec in table.recs:
                    self.tables.add_recs(rec[field.name])
            elif field.relation:
                raise UserError("Fuck")
        table.dirty = False

    def export(self, filename):
        data = {k: v.export() for k, v in self.tables.items() if v.toexport}
        # with open(filename, 'w') as fp:
        fp = io.StringIO()
        json.dump(data, fp, indent=4, default=lambda x: "Zzz")
        return fp


################################################################################################
def ensure_xml_id(self, skip=False):
    """ Create missing external ids for records in ``self``, and return an
        iterator of pairs ``(record, xmlid)`` for the records in ``self``.

    :rtype: Iterable[Model, str | None]
    """
    if skip:
        return ((record, None) for record in self)

    if not self:
        return iter([])

    if not self._is_an_ordinary_table():
        raise Exception(
            "You can not export the column ID of model %s, because the "
            "table %s is not an ordinary table."
            % (self._name, self._table))

    modname = 'omixtory'

    cr = self.env.cr
    cr.execute("""
        SELECT res_id, module, name
        FROM ir_model_data
        WHERE model = %s AND res_id in %s
    """, (self._name, tuple(self.ids)))
    xids = {
        res_id: (module, name)
        for res_id, module, name in cr.fetchall()
    }
    def to_xid(record_id):
        (module, name) = xids[record_id]
        return ('%s.%s' % (module, name)) if module else name

    # create missing xml ids
    missing = self.filtered(lambda r: r.id not in xids)
    if not missing:
        return (
            (record, to_xid(record.id))
            for record in self
        )

    xids.update(
        (r.id, (modname, '%s_%s_%s' % (
            r._table,
            r.id,
            uuid.uuid4().hex[:8],
        )))
        for r in missing
    )
    fields = ['module', 'model', 'name', 'res_id']
    cr.copy_from(io.StringIO(
        u'\n'.join(
            u"%s\t%s\t%s\t%d" % (
                modname,
                record._name,
                xids[record.id][1],
                record.id,
            )
            for record in missing
        )),
        table='ir_model_data',
        columns=fields,
    )
    self.env['ir.model.data'].invalidate_cache(fnames=fields)

    return (
        (record, to_xid(record.id))
        for record in self
    )
