# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . common import next_idx, calc_prefix, MAXIDX


class Client(models.Model):
    _name = "omixtory.client"
    _rec_name = "dc"

    partner_id = fields.Many2one('res.partner', context={'default_is_company': True},
                                 domain=[('is_company', '=', True)])
    dc = fields.Char('Client Name', required=True,
                     states={'normal': [('readonly', True)]})
    idx = fields.Integer("Client Index", default=lambda self: self._next_idx(), required=True,
                     states={'normal': [('readonly', True)]})
    cloud_network_prefix = fields.Char("cloud_network_prefix", required=True,
                     states={'normal': [('readonly', True)]})
    vpn_network_prefix = fields.Char("vpn_network_prefix", required=True,
                     states={'normal': [('readonly', True)]})
    ad_domain = fields.Char("AD domain", config=True, required=True,
                     states={'normal': [('readonly', True)]})
    ldap_base = fields.Char('ldap_base', config=True, required=True,
                     states={'normal': [('readonly', True)]})
    vpn_port = fields.Integer('Openvpn port number', config=True, required=True,
                     states={'normal': [('readonly', True)]})
    vlanid = fields.Integer('VLAN id in cloud', config=True, required=True,
                     states={'normal': [('readonly', True)]})


    site_ids = fields.One2many('omixtory.site', 'client_id', string='Sites')
    host_ids = fields.One2many('omixtory.host', 'client_id', string='Cloud hosts',
                               domain=[('site_id', '=', False)])

    state = fields.Selection([
        ('draft', 'Draft1'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    def _next_idx(self):
        return list(
            set(range(1, MAXIDX)) -
            set(self.search([]).mapped('idx'))
        )[0]

    @api.multi
    def ensure_vlanid(self):
        self.ensure_one()
        if self.vlanid:
            return
        self.vlanid = list(
            set(range(101, 4000)) -
            set(self.search([]).mapped('vlanid'))
        )[0]

        # return next_idx(self.env.cr, 'client', 'idx', 0)
        # self.env.cr.execute(_next_idx_sql.format(tab='client'))
        # res = self.env.cr.fetchone()
        # return res[0] if res else 1

    @api.onchange('site_ids')
    def _onchange_site_ids(self):
        pass

    @api.onchange('idx')
    def _onchange_idx(self):
        # if self.idx and self.idx < 8128:
        self.cloud_network_prefix = calc_prefix(self.idx, 64)
        self.vpn_network_prefix = calc_prefix(self.idx, 160)
        self.vpn_port = 20000 + self.idx

    @api.onchange('dc')
    def _onchange_dc(self):
        if self.dc:
            self.dc = self.dc.lower()
            if re.match('^[a-z]{2,8}$', self.dc):
                self.ad_domain = "ad.{}.omx".format(self.dc)
                self.ldap_base = "dc=ad,dc={},dc=omx".format(self.dc)

    @api.constrains('dc')
    def _validate_name(self):
        if not re.match('^[a-z]{2,8}$', self.dc):
            raise ValidationError('dc must be [a-z0-9]{2,8}!')

    # @api.onchange('state')
    # def _onchange_state(self):
    #     self.site_ids.write({'state': self.state})
    #     self.host_ids.write({'state': self.state})

    def _vars(self):
        vals = {k: self[k] for k, d in self._fields.items()
                if d._attrs and d._attrs['config']}
        vals.update({
            'client': self.dc
        })
        return vals

    def _sites(self):
        return [r.group() for r in self.site_ids if r.state == 'normal']

    def _cloud_hosts(self):
        return [r.name for r in self.env['omixtory.host'].
                search([('client_id', '=', self.id), ('site_id', '=', False), ('state', '=', 'normal')])]

    def _inventory(self):
        return {
                "vars": self._vars(),
                "children": self._sites() + [self.dc + '_cloud']
            }

    @api.multi
    def inventory(self):
        inv = {r.dc: r._inventory() for r in self if r.state == 'normal'}
        inv.update({r.dc + '_cloud': {'hosts': r._cloud_hosts()} for r in self if r.state == 'normal'})
        return inv

    @api.multi
    def write(self, vals):
        # if 'active' in vals:
        #     vals['state'] = 'draft'
        if 'active' in vals:
            vals['state'] = 'draft'
        res = super(Client, self).write(vals)
        if not res:
            return res
        if 'active' in vals or 'state' in vals:
            sites = self.env['omixtory.site'].search([('client_id', 'in', self.ids)])
            hosts = self.env['omixtory.host'].search([('client_id', 'in', self.ids)])
            if 'active' in vals and not vals['active']:
                sites.write({'active': False})
                hosts.write({'active': False})
            if 'state' in vals:
                sites.write({'state': vals['state']})
                hosts.write({'state': vals['state']})
        return res


