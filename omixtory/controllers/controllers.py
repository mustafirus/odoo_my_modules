# -*- coding: utf-8 -*-
import json

from odoo import http

class Omixtory(http.Controller):
    @http.route('/omixtory/inventory', auth='public')
    def index(self, **kw):
        env = http.request.env

        clients = env['omixtory.client'].sudo()
        sites = env['omixtory.site'].sudo()
        hosts = env['omixtory.host'].sudo()
        templates = env['omixtory.host.template'].sudo()

        inventory = {
            "_meta": {
                "hostvars": hosts.search([]).hostvars()
            },
            "all": {
                "hosts": [r.name for r in hosts.search([])],
                "children": [
                    "ungrouped"
                ] + [r.dc for r in clients.search([])] +
                            [r.group() for r in sites.search([])]
            },
            "ungrouped": {}
        }
        inventory.update(clients.search([]).inventory())
        inventory.update(sites.search([]).inventory())
        inventory.update(templates.search([]).inventory())


        return json.dumps(inventory, indent=True)

#     @http.route('/omixtory/omixtory/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('omixtory.listing', {
#             'root': '/omixtory/omixtory',
#             'objects': http.request.env['omixtory.omixtory'].search([]),
#         })

#     @http.route('/omixtory/omixtory/objects/<model("omixtory.omixtory"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('omixtory.object', {
#             'object': obj
#         })