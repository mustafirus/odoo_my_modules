# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Hall(models.Model):
    _name = 'slot_machine_counters.hall'

    name = fields.Char('Name of hall')
    description = fields.Text('Description')
    hub_id = fields.Integer("Hub ID")
    hub_sim = fields.Char("Hub SIM")
    phone = fields.Char("Phone of admin")
    geo = fields.Integer("Geo Location Mark")
    slot_ids = fields.One2many("slot_machine_counters.slot","hall_id","Slots")
    active = fields.Boolean('Active?', default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


class Slot(models.Model):
    _name = 'slot_machine_counters.slot'

    device_id = fields.Integer("Device ID")
    num = fields.Integer("Number")
    type = fields.Char("Game type")
    denomenation = fields.Float()
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    passwd = fields.Char("Password")
    active = fields.Boolean('Active?', default=True)

class SlotShot(models.Model):
    _name = 'slot_machine_counters.slotshot'
    _description = 'SlotShot'

    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    date = fields.Date("Date")
    shotshot_line = fields.One2many('slot_machine_counters.slotshot.line', 'slotshot_id', string='Slotshot Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

class SlotShotLine(models.Model):
    _name = 'slot_machine_counters.slotshot.line'
    _description = 'SlotShot Line'
    _order = 'slotshot_id'

    slotshot_id = fields.Many2one('slot_machine_counters.slotshot', string='SlotShot Reference', required=True, ondelete='cascade', index=True, copy=False)
    iin_begin = fields.Integer("iin")
    out_begin = fields.Integer("out")
    iin_end   = fields.Integer("iin")
    out_end   = fields.Integer("out")
    delta     = fields.Integer("delta",compute='_compute_amount', readonly=True, store=True)
