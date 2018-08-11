# -*- coding: utf-8 -*-

from odoo import models, fields, api


_next_idx_sql = '''
SELECT  idx + 1
FROM    omixtory_{tab} mo
WHERE   NOT EXISTS
        (
        SELECT  NULL
        FROM    omixtory_{tab} mi 
        WHERE   mi.idx = mo.idx + 1
        )
ORDER BY
        idx
LIMIT 1
'''


def _calc_prefix(idx, base):
    n3 = int((idx - 1) / 254) + base
    n2 = (idx - 1) % 254 + 1
    return "10.{}.{}".format(n3, n2)


class Client(models.Model):
    _name = "omixtory.client"
    _rec_name = "dc"

    partner_id = fields.Many2one('res.partner')
    dc = fields.Char('Client Name')
    idx = fields.Integer("Site IDX", default=lambda self: self._next_idx())
    cloud_network_prefix = fields.Char("cloud_network_prefix")
    vpn_network_prefix = fields.Char("vpn_network_prefix")
    ad_domain = fields.Boolean("AD domain")
    ldap_base = fields.Char('ldap_base')

    def _next_idx(self):
        self.env.cr.execute(_next_idx_sql.format(tab='client'))
        res = self.env.cr.fetchone()
        return res[0] if res else 1

    @api.onchange('idx')
    def _onchange_idx(self):
        if self.idx and self.idx < 8128:
            self.cloud_network_prefix = _calc_prefix(self.idx, 64)
            self.vpn_network_prefix = _calc_prefix(self.idx, 160)


class Site(models.Model):
    _name = 'omixtory.site'
    _sql_constraints = [
        ('idx_unique', 'unique(idx)', 'site idx already exists!')
    ]

    name = fields.Char('Name', compute='_compute_name')
    client_id = fields.Many2one('omixtory.client')
    dc = fields.Char('Site name')
    idx = fields.Integer("Site IDX", default=lambda self: self._next_idx())
    box_network_prefix = fields.Char("box_network_prefix")
    default_boxname = fields.Char("Default Box Hostname")

    def _next_idx(self):
        self.env.cr.execute(_next_idx_sql.format(tab='site'))
        res = self.env.cr.fetchone()
        return res[0] if res else 1

    @api.depends('client_id', 'dc')
    def _compute_name(self):
        for rec in self:
            if rec.client_id:
                rec.name = rec.client_id.dc
                if rec.dc:
                    rec.name += " " + rec.dc

    @api.onchange('idx')
    def _onchange_idx(self):
        if self.idx and self.idx < 8128:
            self.box_network_prefix = _calc_prefix(self.idx, 32)


class Host(models.Model):
    _name = 'omixtory.host'

    name = fields.Char('FQDN')
    ip = fields.Char('IP')
    vmid = fields.Char("VMID")
    client_id = fields.Many2one('omixtory.client')
    site_id = fields.Many2one('omixtory.site')
    service_ids = fields.One2many('omixtory.service', 'host_id', 'Services')

    # @api.onchange('site_id')
    # def _onchange_site_id(self):
    #     if self.ip:
    #         self.ip = self.site_id.box_network_prefix + '.' + self.ip.rsplit('.', 1)[1]
