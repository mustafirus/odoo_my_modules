# -*- coding: utf-8 -*-
from odoo import http

# class Omixtory(http.Controller):
#     @http.route('/omixtory/omixtory/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

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