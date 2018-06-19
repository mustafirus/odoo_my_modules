# -*- coding: utf-8 -*-
import json

from odoo import http

class Gambling(http.Controller):
    @http.route('/slot_machine_counters/jackpot/<hub_sn>', auth='public')
    def index(self, hub_sn, **kw):
        jackpots = http.request.env['slot_machine_counters.jackpot']
        jackpots = jackpots.sudo().by_hub_sn(hub_sn)
        vals=[]
        for jackpot in jackpots:
            vals.append({
                'name': jackpot.conf_id.name,
                'value': jackpot.getjack(),
            })
        return http.request.make_response(json.dumps(vals),
                                          [('Content-Type', 'application/json')])

    @http.route('/slot_machine_counters/jackpot/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('slot_machine_counters.listing', {
            'root': '/slot_machine_counters/jackpot',
            'objects': http.request.env['slot_machine_counters.jackpot'].search([]),
        })

    @http.route('/slot_machine_counters/gambling/objects/<model("gambling.gambling"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('slot_machine_counters.object', {
            'object': obj
        })