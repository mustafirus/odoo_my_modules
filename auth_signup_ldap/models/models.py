# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import ldap
import logging
from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.auth_signup.models.res_users import SignupError


_logger = logging.getLogger(__name__)
website_account.MANDATORY_BILLING_FIELDS = ["name"]
website_account.OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "phone", "email", "street", "city", "country_id"]


class ResUsers(models.Model):
    _inherit = 'res.users'

    login = fields.Char(readonly=True)

    @api.model
    def create(self, values):
        if not self.env.context.get('install_mode') \
                and self.env.context.get('no_reset_password'):
            self.env['res.company.ldap'].entry_add(values)
            del values['password']
        return super(ResUsers, self).create(values)

    @api.multi
    def write(self, vals):
        values = vals.copy()
        if values.get('password'):
            try:
                self.env['res.company.ldap'].entry_modify(dict(values, **{'login': self.login}))
                del values['password']
            except SignupError:
                if values.get('raise'):
                    raise
        return super(ResUsers, self).write(values)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def write(self, values):
        if values.get('name'):
            login = self.user_ids.login
            if login:
                try:
                    self.env['res.company.ldap'].entry_modify(dict(values, **{'login': login}))
                except SignupError:
                    if values.get('raise'):
                        raise
        return super(ResPartner, self).write(values)


class CompanyLDAP(models.Model):
    _inherit = 'res.company.ldap'

    def authenticate0(self, login, password):
        return self.authenticate(self.get_ldap_dicts()[0], login, password)

    def entry_add(self, values):
        uid = values['login']
        name = values.get('name')
        names = name.strip().split(' ') if name else []
        modlist = [
            ('objectClass', 'inetOrgPerson'),
            ('uid', uid.encode('utf-8')),
            ('givenName', names[0].encode('utf-8')),
            ('sn', names[-1].encode('utf-8')),
            ('cn', name.encode('utf-8')),
            ('description', 'svami.in.ua self reg'),
            ('userPassword', values['password'].encode('utf-8')),
        ]
        self.entry_add_modify(uid, modlist)

    def entry_modify(self, values):
        uid = values['login']
        modlist = []
        name = values.get('name')
        if name:
            names = name.strip().split(' ') if name else []
            modlist.append((ldap.MOD_REPLACE, 'givenName', names[0].encode('utf-8')))
            modlist.append((ldap.MOD_REPLACE, 'sn', names[-1].encode('utf-8')))
            modlist.append((ldap.MOD_REPLACE, 'cn', name.encode('utf-8')))

        password = values.get('password')
        if password:
            modlist.append((ldap.MOD_REPLACE, 'userPassword', password.encode('utf-8')))

        self.entry_add_modify(uid, modlist, create=False)

    def entry_add_modify(self, uid, modlist, create=True):
        try:
            conf = self.get_ldap_dicts()[0]
            dn = "uid=%s,%s" % (uid, conf['ldap_base'])
            conn = self.connect(conf)
            ldap_password = conf['ldap_password'] or ''
            ldap_binddn = conf['ldap_binddn'] or ''
            conn.simple_bind_s(ldap_binddn.encode('utf-8'), ldap_password.encode('utf-8'))
            if create:
                conn.add_s(dn, modlist)
            else:
                conn.modify_s(dn, modlist)
            conn.unbind()
        except IndexError:
            raise SignupError("LDAP not configured")
        except ldap.ALREADY_EXISTS:
            _logger.error('User Exists.')
            raise SignupError('User Exists.')
        except ldap.LDAPError, e:
            _logger.error('An LDAP exception occurred: %s', e)
            raise SignupError()
