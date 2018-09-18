# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rootfscalc(models.Model):
    _name = 'rootfscalc.rootfscalc'
    # _inherit = 'website'

    name = fields.Char('Email', compute='_compute_name')
    email_to = fields.Char('Email')
    ip = fields.Char('IP')
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
    meta = fields.Char('Metadata', inverse='_inverse_meta', readonly=True)

    @api.depends('email_to', 'ip')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.email_to if rec.email_to else rec.ip

    def _inverse_meta(self):
        mf = False
        for l in self.meta.split('\n'):
            if l == 'Metadata':
                mf = True
                continue
            if mf and l[:5] == 'IP : ':
                self.ip = l[5:]
                return

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