# -*- coding: utf-8 -*-
# import io
import json
import re

import psycopg2

from odoo import http

# sysmodel = re.compile("")
# from odoo.http import content_disposition, request
from odoo.exceptions import UserError
# from omixtory.models.migrator import Export
# import ..migrator
from ..migrator import ExportLump, ImportLump
# from omixtory.migrator import ExportLump

class Omixtory(http.Controller):
    @http.route('/omixtory/import/selectedrows', auth='user', methods=['POST'], type='json')
    def import_selectedrows(self, **kw):
        imp = ImportLump('Zzzz.json', http.request.env)
        # imp.set_env(env)
        return


        dryrun = True
        env = http.request.env
        import_results = []
        with open('Zzzz.json') as fp:
            data = json.load(fp)
        env.cr.execute('SAVEPOINT import')
        for model, mdata in data.items():
            name_create_enabled_fields = {}
            import_result = env[model]\
                .with_context(import_file=True, name_create_enabled_fields=name_create_enabled_fields)\
                .load(mdata['fields'], mdata['datas'])
            if not import_result['ids']:
                raise UserError(import_result['messages'])
            import_results.append(import_result)
            pass
        try:
            if dryrun:
                env.cr.execute('ROLLBACK TO SAVEPOINT import')
                # cancel all changes done to the registry/ormcache
                env.registry.reset_changes()
                # self.pool.reset_changes()
            else:
                env.cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        # Insert/Update mapping columns when import complete successfully
        return import_results

    @http.route('/omixtory/export/selectedrows', auth='user', methods=['POST'], type='json')
    def export_selectedrows(self, model, ids, **kw):
        env = http.request.env
        exp = ExportLump(env[model].browse(ids))
        exp.export('Zzzz.json')
        return

        data = { model: {'dirty': True, 'records': env[model].browse(ids)}}
        while any([v['dirty'] for v in data.values()]):
            for model in list(data):
                Omixtory.scan_fields(data, model, env)

        for model in list(data):
            if model == "omixtory.client":
                pass
            recordset = data[model]['records']
            data[model]['fields'] = []
            for name, attrs in recordset.fields_get().items():
                if model == 'omixtory.host':
                    if name not in ['id', 'active']:
                        continue
                if not attrs.get('exportable', True):
                    continue
                if not attrs.get('store', False):
                    continue
                if attrs.get('type', '') in ['one2many']:
                    continue
                if attrs.get('type', '') in ['many2one', 'many2many']:
                    name += '/id'
                data[model]['fields'].append(name)
            data[model].update(recordset.export_data(data[model]['fields'], raw_data=False))
            del data[model]['records']
            del data[model]['dirty']

        # fp = io.BytesIO()
        with open('Zzzz.json', 'w') as fp:
            json.dump(data, fp, indent=4, default=lambda x: "Zzz")
        pass
        # return request.make_response(fp.getvalue(),
        #     headers=[('Content-Disposition', content_disposition('omixtory.json')),
        #              ('Content-Type', self.content_type)])

    @staticmethod
    def fields_get(rs):
        fields_get = rs.fields_get()
        for k,v in list(fields_get):
            if not v.get('exportable', True):
                continue
            if not v.get('store', False):
                v


    @staticmethod
    def scan_fields(data, model, env):
        if not data[model]['dirty']: return
        recordset = data[model]['records']
        for name, attrs in recordset.fields_get().items():
            if attrs['type'] in ['many2one', 'many2many', 'one2many']:
                relation = attrs['relation']
                if re.match(r"res\.|ir\.|base|report\.|mail\.|omixtory\.host\.template", relation):
                    continue
                new = recordset.mapped(name)
                if not new: continue
                try:
                    old = data[relation]['records']
                except:
                    # data[relation] = {'dirty': False, 'records': env[relation]}
                    old = env[relation]
                diff = new - old
                if diff:
                    new = old | new
                    data[relation] = {
                        'dirty': not re.match(r"res\.|ir\.|base|report\.|mail\.", relation),
                        'records': new
                    }
            elif attrs['type'] == 'reference':
                for rec in recordset:
                    relation = rec[name]._name
                    new = rec[name]
                    if not new: continue
                    try:
                        old = data[relation]['records']
                    except:
                        old = env[relation]
                    new = old | new
                    data[relation] = {
                        'dirty': not re.match("res\.|ir\.|base|report\.|mail\.", relation),
                        'records': new
                    }
                    pass
        data[model]['dirty'] = False

    @http.route('/omixtory/inventory', auth='public')
    def index(self, **kw):
        env = http.request.env

        clients = env['omixtory.client'].sudo()
        sites = env['omixtory.site'].sudo()
        hosts = env['omixtory.host'].sudo()
        boxes = env['omixtory.box'].sudo()
        templates = env['omixtory.host.template'].sudo()
        allhosts = hosts.search([('state', '=', 'normal')])
        allclients = clients.search([('state', '=', 'normal')])
        allsites = sites.search([('state', '=', 'normal')])
        alltemplates = templates.search([])
        allboxes = boxes.search([])

        hostvars = allhosts.hostvars()
        hostvars.update(allboxes.hostvars())

        inventory = {
            "_meta": {
                "hostvars": hostvars
            },
            "all": {
                "hosts": [r.name for r in allhosts],
                "children": [
                    "ungrouped",
                    "pm",
                    "pmd",
                    "arc",
                ] + [r.dc for r in allclients] +
                [r.group() for r in allsites] +
                [r.name for r in alltemplates]
            },
            "ungrouped": {}
        }
        inventory.update(allclients.inventory())
        inventory.update(allsites.inventory())
        inventory.update(alltemplates.inventory())

        return json.dumps(inventory, indent=True)
