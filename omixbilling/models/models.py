# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subscription_ok = fields.Boolean(string='Subscription', default=False,
                               help="Check this box if this priduct is a subscription.")

    @api.onchange('subscription_ok')
    def _onchange_subscription_ok(self):
        if self.subscription_ok:
            self.type = 'service'


class Product(models.Model):
    _inherit = 'product.product'


    @api.onchange('subscription_ok')
    def _onchange_subscription_ok(self):
        if self.subscription_ok:
            self.type = 'service'


class Omixbilling(models.Model):
    _name = 'omixbilling.subscription'

    name = fields.Char(string='Subscription Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one("res.partner", "Partner")
    product_id = fields.Many2one("product.product","Product")
    started = fields.Date('Rental started on')
    torenew = fields.Date('To renew on')
    price = fields.Monetary("Price")
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.user.company_id.id, required=True)
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('omixbilling.subscription') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('omixbilling.subscription') or _('New')

        result = super(Omixbilling, self).create(vals)
        return result
    # @api.depends('value')
    # def _value_pc(self):
    #     self.value2 = float(self.value) / 100