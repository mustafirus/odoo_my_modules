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

    @api.depends('date_start', 'date_end')
    def _get_qty_subscribed(self):
        def last_day_of_month(date):
            if date.month == 12:
                return date.replace(day=31)
            return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)

        for line in self:
            if not line.date_start or not line.date_end:
                line.qty_subscribed = 0.0
                continue
            start = fields.Date.from_string(line.date_start)
            end = fields.Date.from_string(line.date_end)

            s = start
            r = True
            qty = 0.0
            if start > end:
                r = False
            while (r):
                l = last_day_of_month(s)
                e = l + datetime.timedelta(days=1)
                if e > end:
                    e = end
                    r = False
                mdays = l.day
                qty += (e - s).days / mdays
                s = e
            self.qty_subscribed = qty
            pass

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

    renew_qty = fields.Float(string='Quantity to renew', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)


