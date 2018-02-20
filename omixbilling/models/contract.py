# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError

class Contract(models.Model):
    _name = 'omixbilling.contract'

    partner_id = fields.Many2one('res.partner')
    active = fields.Boolean(default=True)


