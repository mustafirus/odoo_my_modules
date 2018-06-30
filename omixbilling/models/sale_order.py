# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError



class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_id = fields.Many2one('omixbilling.contract')

    @api.onchange('partner_id')
    def _onchange_contract_id(self):
        if self.partner_id:
            self.contract_id = self.partner_id.get_default_contract_id()
        pass

    @api.multi
    def _action_confirm(self):
        lines = self.mapped('order_line')
        lines.subsribe()
        return super(SaleOrder, self)._action_confirm()

    @api.multi
    def write(self, vals):
        return super(SaleOrder, self).write(vals)

    # @api.multi
    # def action_done(self):
    #     today = datetime.date.today()
    #     nextmonth = today + relativedelta(months=1)
    #     for order in self:
    #         for line in order.order_line:
    #             if line.product_id.type == 'service':
    #                 line.qty_delivered = line.product_uom_qty
    #                 if line.product_id.subscription_ok:
    #                     self.env["omixbilling.subscription"].create({
    #                         'contract_id': order.contract_id,
    #                         'order_line_id': line.id,
    #                         'started': fields.Date.to_string(today),
    #                         'torenew': fields.Date.to_string(nextmonth),
    #                     # currency_id:
    #                     # company_id:
    #                     })
    #     return super(SaleOrder, self).action_done()



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):

        subscriptions = self.filtered(lambda line: line.product_id.subscription_ok)
        for line in subscriptions:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.qty_subscribed - line.qty_invoiced
                    pass
        others = self.filtered(lambda line: line.product_id.subscription_ok)
        super(SaleOrderLine, others)._get_to_invoice_qty()

    # subscription_id = fields.Many2one('omixbilling.subscription')
    date_start = fields.Date('Rental start')
    date_end = fields.Date('Rental end')
    qty_subscribed = fields.Float(
        compute='_get_qty_subscribed', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    @api.multi
    def subsribe(self):
        sub = self.env["omixbilling.subscription"]
        for line in self:
            if line.product_id.subscription_ok:
                sub.create({
                    'order_line_id': line.id,
                    'qty_subscribed': line.product_uom_qty,
                })



    # float_round(value, precision_digits=None, precision_rounding=None, rounding_method='HALF-UP'):