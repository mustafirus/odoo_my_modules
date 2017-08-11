# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import re
import logging
import werkzeug
from odoo.http import request
from odoo.addons.auth_signup.models.res_users import SignupError
_logger = logging.getLogger(__name__)

class AuthSignupLdap(AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if request.httprequest.method == 'POST':
            chars = set('0123456789.')
            if '@' in qcontext.get("login"):
                qcontext["error"] = _("Incorrect Email.")
            elif not any((c in chars) for c in qcontext.get("login")):
                qcontext["error"] = _("Another user is already registered using this email address.")

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                login = '%s@svami.in.ua' % qcontext.get("login")
                qcontext["login"] = login
                kw["login"] = login
                request.params['login'] = login
                self.do_signup(qcontext)
                return super(AuthSignupLdap, self).web_login(*args, **kw)
            except (SignupError, AssertionError), e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["login"] = qcontext.get("login").replace("@svami.in.ua","")
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error(e.message)
                    qcontext['error'] = _("Could not create a new account.")

        return request.render('auth_signup.signup', qcontext)

    # def get_auth_signup_qcontext(self):
    #     qcontext = super(AuthSignupLdap, self).get_auth_signup_qcontext()
    #     if request.httprequest.method == 'POST':
    #     return qcontext

    # def _signup_with_values(self, token, values):
    #     if '@' in values['login']:
    #         values['login'] = re.sub("@.*$", "", values['login'])
    #     values['login'] = '%s@svami.in.ua' % values['login']
    #     super(AuthSignupLdap, self)._signup_with_values(token, values)


                # class AuthSignupLdap(http.Controller):
#     @http.route('/auth_signup_ldap/auth_signup_ldap/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/auth_signup_ldap/auth_signup_ldap/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('auth_signup_ldap.listing', {
#             'root': '/auth_signup_ldap/auth_signup_ldap',
#             'objects': http.request.env['auth_signup_ldap.auth_signup_ldap'].search([]),
#         })

#     @http.route('/auth_signup_ldap/auth_signup_ldap/objects/<model("auth_signup_ldap.auth_signup_ldap"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('auth_signup_ldap.object', {
#             'object': obj
#         })