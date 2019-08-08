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

    name = fields.Char(string='Subscription Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    contract_id = fields.Many2one('omixbilling.contract', readonly=True, index=True)
    product_id = fields.Many2one(readonly=True, index=True)
    description = fields.Char('Description')

    date_begin = fields.Date('Begin')
    date_torenew = fields.Date('To Renew')
    qty_torenew = fields.Float('Months to renew', digits=dp.get_precision('Product Unit of Measure'))
    auto_renew = fields.Boolean(default=True)
    active = fields.Boolean()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('omixbilling.subscription') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('omixbilling.subscription') or _('New')

        result = super(Subscription, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            if vals['active']:
                if not self.date_begin:
                    today = datetime.date.today()
                    torenew = today + relativedelta.relativedelta(month=self.qty_torenew)
                    vals.update({
                        'date_begin': fields.Date.to_string(today),
                        'date_torenew': fields.Date.to_string(torenew),
                    })
                else:
                    del vals['active']
        result = super(Subscription, self).write(vals)
        return result

    @api.model
    def autorenew(self):
        today = fields.Date.today()
        bycontracts = {}
        for su in self.search([('date_torenew','<=', today),('auto_renew', '=', True)]):
            if not su.contract_id.id in bycontracts:
                bycontracts[su.contract_id] = []
            bycontracts[su.contract_id].append(su)
        for cont in bycontracts.keys():

            for su in bycontracts[cont]:
                pass

