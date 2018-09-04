# -*- coding: utf-8 -*-
from addons.http_routing.models.ir_http import slug
from odoo import http

class Rootfscalc(http.Controller):
    @http.route('/rootfscalc/rootfscalc/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/rootfscalc/rootfscalc/objects/', auth='public', website=True)
    def list(self, **kw):
        return http.request.render('rootfscalc.listing', {
            'root': '/rootfscalc/rootfscalc',
            'objects': http.request.env['rootfscalc.rootfscalc'].search([]),
        })

    @http.route('/rootfscalc/rootfscalc/objects/<model("rootfscalc.rootfscalc"):obj>/', auth='public', website=True)
    def object(self, obj, **kw):
        return http.request.render('rootfscalc.object', {
            'object': obj
        })

    @http.route('/rootfscalc/rootfscalc/objects/add', auth='public', website=True)
    def add(self, **kw):
        return http.request.render('rootfscalc.add', {})
