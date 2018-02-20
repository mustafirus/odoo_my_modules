# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError


class Subscription(models.Model):
    _name = 'omixbilling.subscription'

    name = fields.Char(string='Subscription Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # badge_name = fields.Char(related='badge_id.name', string="Badge Name")
    order_line_id = fields.Many2one('sale.order.line')
    contract_id = fields.Many2one(related='order_line_id.order_id.contract_id', readonly=True)
    partner_id = fields.Many2one(related='order_line_id.order_id.partner_id', readonly=True)
    product_id = fields.Many2one(related='order_line_id.product_id', readonly=True)

    date_begin = fields.Date('Begin')
    date_end = fields.Date('End')
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

