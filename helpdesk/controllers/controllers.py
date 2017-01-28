# -*- coding: utf-8 -*-
from odoo import http

class Helpdesk(http.Controller):
    @http.route('/helpdesk/helpdesk/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/helpdesk/helpdesk/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('helpdesk.listing', {
            'root': '/helpdesk/helpdesk',
            'objects': http.request.env['helpdesk.helpdesk'].search([]),
        })

    @http.route('/helpdesk/helpdesk/objects/<model("helpdesk.helpdesk"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('helpdesk.object', {
            'object': obj
        })
