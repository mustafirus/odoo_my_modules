# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.addons.base.ir.ir_mail_server import MailDeliveryException
from odoo.exceptions import UserError
from odoo.http import request

class Rootfscalc(http.Controller):
    @http.route('/calc', auth='public', website=True)
    def calc(self, **kw):
        if not request.website.website_form_enable_metadata:
            request.website.website_form_enable_metadata = True

        if request and request.session.form_builder_model_model and 'rootfscalc.rootfscalc':
            request.session['rootfscalc_id'] = request.session.form_builder_id
            del request.session['form_builder_model_model']
            del request.session['form_builder_model']
            del request.session['form_builder_id']

        if request.session.rootfscalc_id:
            rootfscalc = request.env['rootfscalc.rootfscalc'].sudo().browse(request.session.rootfscalc_id)
            calcsummary = rootfscalc.summary()
            calctotal = 3331  # calc.total()
            return http.request.render('rootfscalc.result', {
                'calcsummary': calcsummary,
                'calctotal': calctotal,
            })

        return http.request.render('rootfscalc.calc')

    @http.route('/calc/send', type='http', auth="public", methods=['POST'], website=True)
    def calcsend(self, **kw):
        email = kw.get('email')
        if not email:
            return json.dumps({'error_fields': {
                'email': 'Empty email',
            }})
        if email.find('@') == -1:
            return json.dumps({'error_fields': {
                'email': 'Incorrect email',
            }})
        rootfscalc = request.env['rootfscalc.rootfscalc'].sudo().browse(request.session.rootfscalc_id)
        rootfscalc.email_to = kw.get('email')
        template = request.env.ref('rootfscalc.calc_email_template').sudo()
        try:
            mid = template.send_mail(rootfscalc.id, force_send=True, raise_exception=True, email_values=None)
        except MailDeliveryException as e:
            return json.dumps({'error_fields': {
                'email': e.value,
            }})
        return json.dumps({'id': mid})

    @http.route('/calc/reset', type='http', auth="public", methods=['GET'], website=True)
    def calcreset(self, **kw):
        del request.session['rootfscalc_id']
        return request.redirect("/calc")

