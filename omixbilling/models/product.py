# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subscription_ok = fields.Boolean(string='Subscription', default=False,
                               help="Check this box if this product is a subscription.")


