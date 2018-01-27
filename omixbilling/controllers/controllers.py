# -*- coding: utf-8 -*-
from odoo import http

# class Omixbilling(http.Controller):
#     @http.route('/omixbilling/omixbilling/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/omixbilling/omixbilling/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('omixbilling.listing', {
#             'root': '/omixbilling/omixbilling',
#             'objects': http.request.env['omixbilling.omixbilling'].search([]),
#         })

#     @http.route('/omixbilling/omixbilling/objects/<model("omixbilling.omixbilling"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('omixbilling.object', {
#             'object': obj
#         })