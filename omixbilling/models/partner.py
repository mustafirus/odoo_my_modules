# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError

class Partner(models.Model):
    _inherit = "res.partner"

    def get_default_contract_id(self):
        self.ensure_one()
        for contract in self.commercial_partner_id.contract_ids:
            if contract.active and contract.company_id == self.env['res.company']._company_default_get():
                return contract
        return None

    contract_ids = fields.One2many('omixbilling.contract', 'partner_id')

    @api.model
    def create(self, vals):
        p = super(Partner, self).create(vals)
        if not p.commercial_partner_id.contract_ids:
            self.env['omixbilling.contract'].create({'partner_id': p.commercial_partner_id.id})
        return p

    @api.multi
    def write(self, vals):
        return super(Partner, self).write(vals)



