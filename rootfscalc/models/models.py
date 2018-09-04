# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rootfscalc(models.Model):
    _name = 'rootfscalc.rootfscalc'
    # _inherit = 'website'

    workstations = fields.Integer()
    printers = fields.Integer()
    mailserver = fields.Boolean()
    router = fields.Boolean()
    ts = fields.Boolean()
    ads = fields.Boolean()
    fileserver = fields.Boolean()
    backup = fields.Boolean()
    oousers = fields.Boolean("Out of office users")
    security = fields.Selection([
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
    ])
    tariff = fields.Selection([
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('VIP', 'VIP'),
    ])

    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        self.value2 = float(self.value) / 100