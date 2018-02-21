# -*- coding: utf-8 -*-
# from dateutil.relativedelta import relativedelta
# import odoo.addons.decimal_precision as dp
# from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
# from odoo.exceptions import UserError, AccessError
import datetime
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
import dateutil.relativedelta as relativedelta

class Subscription(models.Model):
    _name = 'omixbilling.subscription'

    def _last_day_of_month(self, qty):
        date = datetime.date.today() + relativedelta.relativedelta(month=qty)
        return date.replace(day=1) - datetime.timedelta(days=1)

    @api.depends('date_begin', 'date_end')
    def _get_qty_subscribed(self):

        for sub in self:
            if not sub.date_begin or not sub.date_end:
                sub.qty_subscribed = 0.0
                continue
            start = fields.Date.from_string(sub.date_begin)
            end = fields.Date.from_string(sub.date_end)

            s = start
            r = True
            qty = 0.0
            if start > end:
                r = False
            while (r):
                l = self._last_day_of_month(s)
                e = l + datetime.timedelta(days=1)
                if e > end:
                    e = end
                    r = False
                mdays = l.day
                qty += (e - s).days / mdays
                s = e
            sub.qty_subscribed = qty
            pass

    name = fields.Char(string='Subscription Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # badge_name = fields.Char(related='badge_id.name', string="Badge Name")
    order_line_id = fields.Many2one('sale.order.line')
    contract_id = fields.Many2one(related='order_line_id.order_id.contract_id', readonly=True)
    partner_id = fields.Many2one(related='order_line_id.order_id.partner_id', readonly=True)
    product_id = fields.Many2one(related='order_line_id.product_id', readonly=True)

    date_begin = fields.Date('Begin')
    date_end = fields.Date('End')
    active = fields.Boolean(default=True)

    qty_subscribed = fields.Float(
        compute='_get_qty_subscribed', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('omixbilling.subscription') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('omixbilling.subscription') or _('New')
            qty = int(vals['qty_subscribed'])

            vals.update({
                'date_begin': fields.Date.today(),
                'date_end': fields.Date.to_string(self._last_day_of_month(qty)),
            })

        result = super(Subscription, self).create(vals)
        return result

