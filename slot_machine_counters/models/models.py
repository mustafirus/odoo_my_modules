# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import urllib2
import werkzeug.urls
import string

class Hall(models.Model):
    _name = 'slot_machine_counters.hall'

    name = fields.Char('Name of hall')
    description = fields.Text('Description')
    hub_sn = fields.Char("Hub SN")
    hub_sim = fields.Char("Hub SIM")
    phone = fields.Char("Phone of admin")
    gpslat = fields.Float("Geo Lat")
    gpslng = fields.Float("Geo Long")
    slot_ids = fields.One2many("slot_machine_counters.slot","hall_id","Slots")
    active = fields.Boolean('Active?', default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


class Slot(models.Model):
    _name = 'slot_machine_counters.slot'

    name = fields.Char("Name",compute='_compute_name', readonly=True, store=True)
    index = fields.Integer("Index")
    dev_sn = fields.Char("SN")
    type = fields.Char("Game type")
    denomenation = fields.Monetary("Denomenation",currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    active = fields.Boolean('Active?', default=True)

    @api.depends('dev_sn')
    def _compute_name(self):
        for rec in self:
            dev_sn = rec.dev_sn if rec.dev_sn else "Unknown"
            rec.name = "%s" % dev_sn


class SlotShot(models.Model):
    _name = 'slot_machine_counters.slotshot'
    _description = 'SlotShot'

    name = fields.Char("Name",compute='_compute_name', readonly=True, store=True)
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    date = fields.Date("Date")
    slotshot_lines = fields.One2many('slot_machine_counters.slotshot.line', 'slotshot_id', string='Slotshot Lines')

    @api.depends('hall_id', 'date')
    def _compute_name(self):
        for rec in self:
            rec.name = "%s/%s" % (rec.hall_id.name, rec.date) if rec.date and rec.hall_id else "---"


    def _get_data_rrd(self, date, devid):
        GAMBLING_ENDPOINT = 'http://localhost:4000/counters'
        GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000/counters?'
        date = string.replace(date, '-', '')
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        reqargs = werkzeug.url_encode({
            'date': date,
            'devid': devid,
        })
        try:
            req = urllib2.Request(GAMBLING_ENDPOINT + reqargs, None, headers)
            content = urllib2.urlopen(req, timeout=200).read()
        except urllib2.HTTPError:
            raise
        content = json.loads(content)
        err = content.get('error')
        if err:
            e = urllib2.HTTPError()
            e.msg = err
            raise e
        return content

    @api.multi
    def get_data(self):
        self.ensure_one()
        if not self.hall_id:
            return
        ids = self.hall_id.slot_ids
        slotline = self.env['slot_machine_counters.slotshot.line']
        existing = slotline.browse(self.slotshot_lines._ids)
        existing.unlink()
        for slot in ids:
            rrd = self._get_data_rrd(self.date, slot.dev_sn)
            vals = {
                'slotshot_id': self.id,
                'slot_id': slot.id,
                'index': slot.index,
                'iin_begin': rrd['iinB'] if rrd['iinB'] else rrd['betB'],
                'iin_end':   rrd['iinE'] if rrd['iinE'] else rrd['betE'],
                'out_begin': rrd['outB'] if rrd['outB'] else rrd['winB'],
                'out_end':   rrd['outE'] if rrd['outE'] else rrd['winE'],
            }
            slotline.create(vals)
        a=1

class SlotShotLine(models.Model):
    _name = 'slot_machine_counters.slotshot.line'
    _description = 'SlotShot Line'
    _order = 'slotshot_id,index'

    slotshot_id = fields.Many2one('slot_machine_counters.slotshot', string='SlotShot Reference', required=True, ondelete='cascade', index=True, copy=False)
    index = fields.Integer("Index")
    slot_id = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_begin = fields.Integer("in")
    iin_end   = fields.Integer("IN")
    out_begin = fields.Integer("out")
    out_end   = fields.Integer("OUT")
    iin       = fields.Integer("IN-in",compute='_compute_in', readonly=True, store=True)
    out       = fields.Integer("OUT-out",compute='_compute_out', readonly=True, store=True)
    credit     = fields.Integer("Credit",compute='_compute_credit', readonly=True, store=True)
    amount     = fields.Monetary("$",compute='_compute_amount', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='slot_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')

    @api.depends('iin_begin','out_begin','iin_end','out_end')
    def _compute_credit(self):
        for rec in self:
            rec.credit = (rec.iin_end - rec.iin_begin) - (rec.out_end - rec.out_begin)

    @api.depends('iin_begin','iin_end')
    def _compute_in(self):
        for rec in self:
            rec.iin = (rec.iin_end - rec.iin_begin)

    @api.depends('out_begin','out_end')
    def _compute_out(self):
        for rec in self:
            rec.out = (rec.out_end - rec.out_begin)

    @api.depends('credit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.credit * rec.slot_id.denomenation
