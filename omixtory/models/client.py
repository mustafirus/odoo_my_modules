# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . common import calc_prefix, MAXIDX


class Client(models.Model):
    _name = "omixtory.client"
    _rec_name = "dc"
    _order = 'idx'

    _sql_constraints = [
        ('idx_unique', 'unique(idx)', 'client idx already exists!'),
        ('vpn_port_unique', 'unique(vpn_port)', 'client vpn port already exists!'),
    ]

    partner_id = fields.Many2one('res.partner', context={'default_is_company': True},
                                 domain=[('is_company', '=', True)])
    dc = fields.Char('Client Name', required=True,
                     states={'normal': [('readonly', True)]},
                     help="Domain component")
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
    site_ids_str = fields.Char(string='Sites', compute='_compute_site_ids_str')
    host_ids = fields.One2many('omixtory.host', 'client_id', string='Cloud hosts',
                               domain=[('site_id', '=', False)])
    host_ids_str = fields.Char(string='Cloud hosts', compute='_compute_host_ids_str')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    def _next_idx(self):
        return list(
            set(range(1, MAXIDX)) -
            set(self.with_context(active_test=False).search([]).mapped('idx'))
        )[0]

    api.depends('site_ids.dc')
    def _compute_site_ids_str(self):
        for rec in self:
            rec.site_ids_str = ','.join(rec.mapped('site_ids.dc'))

    api.depends('host_ids.dc')
    def _compute_host_ids_str(self):
        for rec in self:
            rec.host_ids_str = ','.join(rec.mapped('host_ids.dc'))

    @api.multi
    def ensure_vlanid(self):
        self.ensure_one()
        if self.vlanid:
            return
        self.vlanid = list(
            set(range(101, 4000)) -
            set(self.with_context(active_test=False).search([]).mapped('vlanid'))
        )[0]

        # return next_idx(self.env.cr, 'client', 'idx', 0)
        # self.env.cr.execute(_next_idx_sql.format(tab='client'))
        # res = self.env.cr.fetchone()
        # return res[0] if res else 1

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
            # if re.match('^[a-z]{2,8}$', self.dc):
            self.ad_domain = "ad.{}.omx".format(self.dc)
            self.ldap_base = "dc=ad,dc={},dc=omx".format(self.dc)

    @api.constrains('dc')
    def _validate_name(self):
        for rec in self:
            if not re.match('^[a-z]{2,8}$', rec.dc):
                raise ValidationError('dc must be [a-z0-9]{2,8}!')

    @api.constrains('vlanid')
    def _validate_vlanid(self):
        self.ensure_one()
        if self.vlanid and self.vlanid in self.with_context(active_test=False).search([('id','!=',self.id)]).mapped('vlanid'):
            raise ValidationError('duplicate vlanid!')

    # @api.onchange('state')
    # def _onchange_state(self):
    #     self.site_ids.write({'state': self.state})
    #     self.host_ids.write({'state': self.state})

    def get_domain(self):
        return self.dc + ".omx" if self.dc else '';

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


