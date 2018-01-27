# -*- coding: utf-8 -*-
from odoo import http

# class Privat24Sync(http.Controller):
#     @http.route('/privat24_sync/privat24_sync/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/privat24_sync/privat24_sync/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('privat24_sync.listing', {
#             'root': '/privat24_sync/privat24_sync',
#             'objects': http.request.env['privat24_sync.privat24_sync'].search([]),
#         })

#     @http.route('/privat24_sync/privat24_sync/objects/<model("privat24_sync.privat24_sync"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('privat24_sync.object', {
#             'object': obj
#         })