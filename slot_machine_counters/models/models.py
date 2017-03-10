# -*- coding: utf-8 -*-

from odoo import models, fields, api

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
    denomenation = fields.Float("Denomenation")
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
            vals = {
                'slotshot_id': self.id,
                'slot_id': slot.id,
                'index': slot.index,
                'iin_begin': 1,
                'iin_end': 45,
                'out_begin': 2,
                'out_end':4,
            }
            slotline.create(vals)
        a=1

class SlotShotLine(models.Model):
    _name = 'slot_machine_counters.slotshot.line'
    _description = 'SlotShot Line'
    _order = 'slotshot_id,index'

    index = fields.Integer("Index")
    slot_id = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_begin = fields.Integer("In Begin")
    iin_end   = fields.Integer("In End")
    out_begin = fields.Integer("Out Begin")
    out_end   = fields.Integer("Out End")
    delta     = fields.Integer("Delta",compute='_compute_amount', readonly=True, store=True)
    slotshot_id = fields.Many2one('slot_machine_counters.slotshot', string='SlotShot Reference', required=True, ondelete='cascade', index=True, copy=False)

    @api.depends('iin_begin','out_begin','iin_end','out_end')
    def _compute_amount(self):
        for rec in self:
            rec.delta = (rec.iin_end - rec.iin_begin) - (rec.out_end - rec.out_begin)

