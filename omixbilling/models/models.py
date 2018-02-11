# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _



class Contract(models.Model):
    _name = 'omixbilling.contract'

    partner_id = fields.Many2one('res.partner')
    active = fields.Boolean(default=True)


class Subscription(models.Model):
    _name = 'omixbilling.subscription'

    name = fields.Char(string='Subscription Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # badge_name = fields.Char(related='badge_id.name', string="Badge Name")
    contract_id = fields.Many2one('omixbilling.contract')
    order_line_id = fields.Many2one('sale.order.line')
    partner_id = fields.Many2one(related='contract_id.partner_id', readonly=True)
    product_id = fields.Many2one(related='order_line_id.product_id', readonly=True)

    started = fields.Date('Rental started on')
    torenew = fields.Date('To renew on')
    active = fields.Boolean(default=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('omixbilling.subscription') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('omixbilling.subscription') or _('New')

        result = super(Subscription, self).create(vals)
        return result
    # @api.depends('value')
    # def _value_pc(self):
    #     self.value2 = float(self.value) / 100


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

class Partner(models.Model):
    _inherit = "res.partner"

    default_contract_id = fields.Many2one('omixbilling.contract',
                                          default=lambda self: self.env['omixbilling.contract'].
                                          create({'partner_id': self.id}) )
    contract_ids = fields.Many2one('omixbilling.contract', 'partner_id')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_id = fields.Many2one('omixbilling.contract')

    @api.onchange('partner_id')
    def _onchange_contract_id(self):
        if self.partner_id:
            self.contract_id = self.partner_id.default_contract_id

    @api.multi
    def action_done(self):
        today = datetime.date.today()
        nextmonth = today + relativedelta(months=1)
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'service':
                    line.qty_delivered = line.product_uom_qty
                    if line.product_id.subscription_ok:
                        self.env["omixbilling.subscription"].create({
                            'contract_id': order.contract_id,
                            'order_line_id': line.id,
                            'started': fields.Date.to_string(today),
                            'torenew': fields.Date.to_string(nextmonth),
                        # currency_id:
                        # company_id:
                        })
        return super(SaleOrder, self).action_done()

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
