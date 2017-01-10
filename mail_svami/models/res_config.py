# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import dns.resolver

def is_alias_on_svami(domain_alias):
    try:
        answers = dns.resolver.query(domain_alias, 'MX')
    except dns.exception.DNSException:
        return False
    for server in answers:
        a=str(server.exchange)
        if a == 'svami.in.ua.':
            return True
    return False


class BaseConfiguration(models.TransientModel):
    _inherit = 'base.config.settings'

    use_svami = fields.Boolean("Use svami mail", help="Configure svami mail"
                                                      "This requires subscription to svami")
    @api.model
    def get_default_use_svami(self, fields):
        use_svami = self.env["ir.config_parameter"].get_param("svami.use_svami", default=False)
        return {'use_svami': use_svami}

    @api.one
    def set_use_svami(self):
        use_svami = self.use_svami
        alias_domain = self.alias_domain
        alias_domain_old = self.env['ir.config_parameter'].get_param("svami.use_svami")
        mail_server= self.env['ir.mail_server'].sudo().search([('name', '=', 'svami')])
        fetchmail_server= self.env['fetchmail.server'].sudo().search([('name', '=', 'svami')])
        if not use_svami or not is_alias_on_svami(alias_domain):
            if len(mail_server) > 0:
                mail_server.unlink()
                fetchmail_server.unlink()
            self.env['ir.config_parameter'].set_param("svami.use_svami", False)
            return
        if (alias_domain !=  alias_domain_old and len(mail_server) > 0) or len(mail_server) > 1:
            mail_server.unlink()
            fetchmail_server.unlink()

        mail_server.create(
            {'name': "svami", 'smtp_host': "mail.svami.in.ua", 'smtp_port': "587", 'smtp_user': "odoo@"+alias_domain,
             'smtp_encryption': "starttls"}
        )
        fetchmail_server.create(
            {'name': "svami", 'server': "mail.svami.in.ua", 'port': "993",
             'type': 'imap', 'is_ssl': True, 'user': "odoo@" + alias_domain}
        )
        self.env['ir.config_parameter'].set_param("svami.use_svami", alias_domain)


    # @api.depends('use_svami')
    # def onchange_use_svami(self):
    #     a = self.use_svami
    #     if self.use_svami:
    #         return {
    #             'warning': {
    #                 'title': _('Warning!'),
    #                 'message': _('Check creditials in svami outgoing and incoming servers settings \n'),
    #             }
    #         }


    #    @api.onchange('alias_domain')
#    def onchange_svami(self):
#        c = self.alias_domain_changed
#        if self.use_svami:
#            if self.alias_domain != self.env['ir.config_parameter'].get_param("mail.catchall.domain"):
#                self.alias_domain_changed = True
#        c = self.alias_domain_changed
#        a=1

