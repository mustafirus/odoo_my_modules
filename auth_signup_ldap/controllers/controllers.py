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
                # u'duplicate key value violates unique constraint "res_users_login_key"
                # DETAIL:  Key(login) = (aas11 @ svami. in.ua) already
                # exists.
                # '
                # if request.env["res.users"].sudo().search_count([("login", "=", qcontext.get("login"))]):
                #     qcontext["login"] = qcontext.get("login").replace("@svami.in.ua","")
                #     qcontext["error"] = _("Another user is already registered using this email address.")
                # else:
                qcontext["login"] = qcontext.get("login").replace("@svami.in.ua", "")
                if e.message.find("duplicate key value violates unique constraint") != -1:
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error(e.message)
                    qcontext['error'] = _("Could not create a new account.")

        qcontext["signup"] = True
        return request.render('auth_signup.signup', qcontext)

    @http.route('/my/reset_password', type='http', auth='user', website=True)
    def web_my_reset_password(self, *args, **kw):
        qcontext = request.params.copy()
        qcontext.update(self.get_auth_signup_config())
        qcontext['token'] = 'reset_password_auth_user'
        qcontext['login'] = request.env.user.login
        qcontext['name'] = request.env.user.name

        if not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                assert qcontext.get('password'), "Password empty; please retype it."
                assert qcontext.get('password') == qcontext.get(
                    'confirm_password'), "Passwords do not match; please retype them."
                vals = {
                    'login': request.env.user.login,
                    'oldpassword': qcontext.get('oldpassword'),
                    'password': qcontext.get('password'),
                }
                request.env.user.write(vals)
                return request.redirect('/my/home')
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except AssertionError, e:
                qcontext['error'] = e.message or e.name
            except Exception, e:
                _logger.exception('error when resetting password: {}'.format(e.message or e.name))
                qcontext['error'] = _("Could not reset your password")

        return request.render('auth_signup.reset_password', qcontext)
