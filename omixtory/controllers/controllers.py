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
                            [r.group() for r in allsites] + [r.name for r in alltemplates]
            },
            "ungrouped": {}
        }
        inventory.update(allclients.inventory())
        inventory.update(allsites.inventory())
        inventory.update(alltemplates.inventory())


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