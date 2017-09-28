# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class TransferPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    @api.multi
    def render(self, reference, amount, currency_id, partner_id=False, values=None):
        rec = self
        if self.provider == 'transfer':
            rec = self.with_context(submit_txt='Order Now')
        return super(TransferPaymentAcquirer, rec).render(reference, amount, currency_id, partner_id, values)

