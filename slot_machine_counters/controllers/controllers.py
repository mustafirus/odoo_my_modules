# -*- coding: utf-8 -*-
from odoo import http

# class Gambling(http.Controller):
#     @http.route('/slot_machine_counters/gambling/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/slot_machine_counters/gambling/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('slot_machine_counters.listing', {
#             'root': '/slot_machine_counters/gambling',
#             'objects': http.request.env['slot_machine_counters.gambling'].search([]),
#         })

#     @http.route('/slot_machine_counters/gambling/objects/<model("gambling.gambling"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('slot_machine_counters.object', {
#             'object': obj
#         })