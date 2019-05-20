import json
from datetime import datetime
from odoo.exceptions import MissingError
MAXINT32=2**31-1

class TableDict(dict):

    def add(self, k, v, lump):
        self[k] = t = Table(k, v, lump.env, lump.xids)
        return t


class Field:
    def __init__(self, table, name, attrs):
        self.table = table
        self.name = name
        self.type = attrs['type']
        self.relation = attrs['relation'] if 'relation' in attrs else None
        self.required = attrs['required']

    def is_xid(self):
        if self.name == 'id':
            return True
        if self.type in ["many2one"]:
            return True
        return False

    def from_json(self, val):
        if not val:
            return val
        if self.name == 'id':
            return self.table.xids[val][1]
        if self.type in ["datetime", "date"]:
            return datetime.fromtimestamp(val)
        if self.type in ["many2one"]:
            return self.table.xids[val][1] or MAXINT32
        if self.type in ["reference"]:
            model, id = self.table.xids[val]
            return "{},{}".format(model, id or 0)
        return val


class Table:
    def __init__(self, k, v, env, xids):
        self.name = k
        self.recs = env[k]
        self.fieldlist = v['fields']
        self.rows = v['rows']
        self.reorder_id()
        self.fields = []
        self.xids = xids
        attrs = self.recs.fields_get()
        for f in self.fieldlist:
            self.fields.append(Field(self, f, attrs[f]))

    def reorder_id(self):
        idx = self.fieldlist.index('id')
        self.fieldlist.insert(0,self.fieldlist.pop(idx))
        for r in self.rows:
            r.insert(0,r.pop(idx))

    def collect_xids(self):
        indexes = list(map(lambda f,i: i if f.is_xid() else None, self.fields, range(0,len(self.fields))))
        xids = {}
        for row in self.rows:
            for i in filter(lambda i: i is not None and row[i], indexes):
                xids[row[i]] = (self.fields[i].relation or self.name, None)
        return xids

    def enable_trigger(selt, cr, table, enable):
        ALTER_QUERY = "ALTER TABLE {table} {action} TRIGGER ALL"
        query = ALTER_QUERY.format(table=table, action="ENABLE" if enable else "DISABLE")
        cr.execute(query)

    # def query_insert(self, num):
    #     cols = [ f.name for f in self.fields if f.required ]
    #     if cols:
    #         row = [ 0 for _ in cols ]
    #         rows = [row for _ in range(0, num)]
    #         params = [tuple(row[i] for i in range(0, len(cols))) for row in rows]
    #     else:
    #         params = []
    #
    #     table = self.recs._table
    #     cr = self.recs.env.cr
    #     if cols:
    #         query = "INSERT INTO {table} ({cols}) VALUES {rows} RETURNING id".format(
    #             table=table,
    #             cols=",".join(cols),
    #             rows=",".join("%s" for _ in range(0, num)),
    #         )
    #     else:
    #         query = "INSERT INTO {table} VALUES {rows} RETURNING id".format(
    #             table=table,
    #             rows=",".join("(DEFAULT)" for _ in range(0, num)),
    #         )
    #     self.enable_trigger(cr, table, False)
    #     cr.execute(query, params)
    #     rows = cr.fetchall()
    #     self.enable_trigger(cr, table, True)
    #     return [row[0] for row in rows]

    # def create_missing(self, xids):
    #     ids = self.query_insert(len(xids))
    #     recs = self.recs.browse(ids)
    #     imd_data_list = map(lambda x, r: {'xml_id': x, 'record': r}, xids, recs)
    #     self.recs.env['ir.model.data']._update_xmlids(imd_data_list)
    #     return

    def insert_recs(self, xids):
        field_list = [f.name for f in self.fields[1:]]
        table = self.recs._table
        rows = []
        imd_xids = []
        for row in self.rows:
            if row[0] in xids:
                imd_xids.append(row[0])
                rows.append(
                    tuple(self.fields[i].from_json(row[i]) for i in range(1, len(self.fields)))
                )
        query = "INSERT INTO {table} ({cols}) VALUES {rows} RETURNING id".format(
            table=table, cols=",".join(field_list), rows = ",".join("%s" for _ in range(0, len(rows))),
        )
        cr = self.recs.env.cr
        self.enable_trigger(cr, table, False)
        # z1 = cr.mogrify(query, rows)
        cr.execute(query, rows,)
        rows = cr.fetchall()
        self.enable_trigger(cr, table, True)
        imd_ids = [row[0] for row in rows]
        imd_data_list = map(lambda x, id: {'xml_id': x, 'record': self.recs.browse(id)}, imd_xids, imd_ids)
        self.recs.env['ir.model.data']._update_xmlids(imd_data_list)

    def update_recs(self):
        field_list = [f.name for f in self.fields[1:]]
        query = 'UPDATE "{}" SET {} WHERE id IN %s'.format(
            self.recs._table, ','.join('"{}"=%s'.format(name) for name in field_list),
        )
        ids = []
        cr = self.recs.env.cr
        for row in self.rows:
            row = [self.fields[i].from_json(row[i]) for i in range(0, len(self.fields))]
            cr.execute(query, row[1:] + [tuple(row[0:1])])
            if cr.rowcount != 1:  # len(self.rows)
                raise MissingError(
                    'One of the records you are trying to modify has already been deleted (Document type: %s).' % self.recs._description)
            ids.append(row[0])
        self.recs.invalidate_cache(ids=ids)
        return


class ImportLump:
    def __init__(self, fp, env):
        self.tables = TableDict()
        self.xids = {}
        self.env = env

        # with open(filename) as fp:
        data = json.load(fp)
        for k, v in data.items():
            t = self.tables.add(k, v, self)
            self.xids.update(t.collect_xids())

        self.lookup_ids(env)
        self.insert_recs()
        self.lookup_ids(env)
        for t in self.tables.values():
            t.update_recs()
        pass

    def lookup_ids(self,env):
        xids_by_model = {}
        for xid, (model, res_id) in self.xids.items():
            xids_by_model.setdefault(model,[]).append(xid)
        imd = env['ir.model.data']
        for model, xids in xids_by_model.items():
            model = env[model]
            for row in imd._lookup_xmlids(xids, model):
                d_id, d_module, d_name, d_model, d_res_id, d_noupdate, r_id = row
                if r_id:
                    xml_id = '%s.%s' % (d_module, d_name)
                    self.xids[xml_id] = (d_model, r_id)
                else:
                    imd.browse(d_id).unlink()
            pass

        # query = "select format('%%s.%%s', module, name) as xid, model, res_id from ir_model_data where (module,name) in %s;"
        # env.cr.execute(query, (tuple(tuple(x.split('.', 1)) for x in self.xids),))
        # for xid in env.cr.fetchall():
        #     self.xids[xid[0]] = xid[1:3]

    def insert_recs(self):
        to_insert = {}
        for xid, (model, res_id) in self.xids.items():
            if not res_id:
                to_insert.setdefault(model,[]).append(xid)

        for t,xid in to_insert.items():
            self.tables[t].insert_recs(xid)

