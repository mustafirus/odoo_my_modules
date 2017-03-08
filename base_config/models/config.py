# -*- coding: utf-8 -*-

from odoo import models, api
import vars

class BaseConfig(models.TransientModel):
    _inherit = 'base.config.settings'

    @api.model
    def _set_default_mail_catchall_domain(self):
        mail_server= self.env['ir.mail_server'].sudo().search([('name', '=', 'localhost')])
        fetchmail_server= self.env['fetchmail.server'].sudo().search([('name', '=', 'localhost')])

        # mail_server.create(
        #     {'name': "svami", 'smtp_host': "mail.svami.in.ua", 'smtp_port': "587",
        #      'smtp_user': mailbox + "@odoo.svami.in.ua",
        #      'smtp_encryption': "starttls"}
        # )
        if len(fetchmail_server) == 0:
            fetchmail_server.create(
                {'name': "localhost", 'server': "localhost", 'port': "143",
                 'type': 'imap', 'is_ssl': False, 'user': "odoo", 'password' : vars.odoo_mail_password} #
            )
        self.env['ir.config_parameter'].set_param("mail.catchall.domain", vars.alias_domain)


