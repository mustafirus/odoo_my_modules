# -*- coding: utf-8 -*-

from odoo import models, api
import vars

class BaseConfig(models.TransientModel):
    _inherit = 'base.config.settings'

    @api.model
    def _set_default_mail_catchall_domain(self):
        fetchmail_server= self.env['fetchmail.server'].sudo().search([('name', '=', 'localhost')])
        if len(fetchmail_server) == 0:
            fetchmail_server.create(
                {'name': "localhost", 'server': "localhost", 'port': "143",
                 'type': 'imap', 'is_ssl': False, 'user': "odoo", 'password' : vars.mail_odoo_password}
            )
        self.env['ir.config_parameter'].set_param("mail.catchall.domain", vars.alias_domain)

        ldap_server= self.env['res.company.ldap'].sudo().search([('ldap_server', '=', '127.0.0.1')])
        company_id = self.env.user.company_id
        if len(ldap_server) == 0:
            ldap_server.create(
                {'ldap_base': vars.ldap_base, 'ldap_filter': "(&(objectClass=inetOrgPerson)(mail=%s))",
                 'company': company_id.id }
            )



