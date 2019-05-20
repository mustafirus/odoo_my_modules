# -*- coding: utf-8 -*-
# import io
import io
import json

from odoo import http

from odoo.exceptions import UserError
from odoo.http import content_disposition, serialize_exception, Response
from odoo.tools import html_escape
from ..migrator import ExportLump, ImportLump
from odoo.tools.translate import _


class Omixtory(http.Controller):
    @http.route('/omixtory/export/selectedrows', auth='user', methods=['POST'], type='http')
    def export_selectedrows(self, model, ids, **kw):
        try:
            env = http.request.env
            ids = [ int(i) for i in ids.split(',')]
            exp = ExportLump(env[model].browse(ids))
            fp = exp.export()
            return http.request.make_response(fp.getvalue(),
                headers=[('Content-Disposition', content_disposition('omixtory.json')),
                         ('Content-Type', 'application/json;charset=utf8')])
        except Exception as e:
            return http.request.make_response(html_escape(json.dumps({
                'title': _('Error'),
                'message': _('Error while export!') + str(e)
            })))

    @http.route('/omixtory/import/selectedrows', auth='user', methods=['POST'], type='http')
    def import_selectedrows(self, file, **kw):
        try:
            env = http.request.env
            cr = env.cr
            cr.execute('SAVEPOINT import_selectedrows')
            # raise UserError('fuuuuck')
            # 'file': file.read(),
            # 'file_name': file.filename,
            # 'file_type': file.content_type,

            ImportLump(io.TextIOWrapper(file, encoding='utf-8'), env)
            cr.execute('RELEASE SAVEPOINT import_selectedrows')
            return http.request.make_response(json.dumps({
                'title': _('Done'),
                'message': _('All done!')
            }), [('Content-Type', 'application/json')])
        except Exception as e:
            cr.execute('ROLLBACK TO SAVEPOINT import_selectedrows')
            return http.request.make_response(json.dumps({
                'title': _('Error'),
                'message': _('Error while export!' + str(e))
            }), [('Content-Type', 'application/json')])

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
