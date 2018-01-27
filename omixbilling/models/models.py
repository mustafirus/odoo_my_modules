# -*- coding: utf-8 -*-

from odoo import models, fields, api

class omixbilling(models.Model):
    _name = 'omixbilling.subscription'

    partner_id = fields.Many2one("res_partner", "Partner")
    product_id = fields.Many2one("product.product","Product")
    started = fields.Date('Rental started on')
    torenew = fields.Date('To renew on')
    price = fields.Monetary("Price", string="Price")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)

    # @api.depends('value')
    # def _value_pc(self):
    #     self.value2 = float(self.value) / 100