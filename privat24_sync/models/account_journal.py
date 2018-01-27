# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _today(self):
        return fields.date.today()

    bank_statements_source = fields.Selection(selection_add=[("privat24_import", "Privat24 Import")])
    privat24_login = fields.Char()
    privat24_pass = fields.Char()
    privat24_savepass = fields.Boolean()
    privat24_session = fields.Char()
    privat24_session_exp = fields.Integer()
    privat24_lastsync = fields.Date(default=_today)

    @api.multi
    def import_statement_privat24(self):
        return {
            'name': 'Import',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'privat24.import',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('privat24_sync.account_bank_statement_import_view').id,
            'context': {'default_journal_id': self.id,
                        'default_privat24_login': self.privat24_login,
                        'default_privat24_pass': self.privat24_pass,
                        'default_privat24_lastsync': self.privat24_lastsync,
                        'default_privat24_savepass': self.privat24_savepass, },
        }
