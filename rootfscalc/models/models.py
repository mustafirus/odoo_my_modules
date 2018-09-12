# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rootfscalc(models.Model):
    _name = 'rootfscalc.rootfscalc'
    # _inherit = 'website'

    meta = fields.Char('Metadata')
    email_to = fields.Char('Email')
    workstations = fields.Integer()
    printers = fields.Integer()
    mailserver = fields.Boolean()
    router = fields.Boolean()
    ts = fields.Boolean()
    ads = fields.Boolean()
    fileserver = fields.Boolean()
    backup = fields.Boolean()
    oousers = fields.Boolean("Out of office users")
    security = fields.Selection([
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
    ])
    tariff = fields.Selection([
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('vip', 'VIP'),
    ])


    @api.multi
    def summary(self):
        self.ensure_one()
        s = '''
            {rec.workstations} workstations,
            {rec.printers} printers,
            {rec.mailserver} mailserver,
            {rec.router} router,
            {rec.ts} ts,
            {rec.ads} ads,
            {rec.fileserver} fileserver,
            {rec.backup} backup,
            {rec.oousers} oousers,
            {rec.security} security,
        '''.format(rec=self)
        return s