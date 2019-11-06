# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . common import next_idx, calc_prefix, calc_vpn_ip, MAXIDX


class Site(models.Model):
    _name = 'omixtory.site'
    _rec_name = "dc"
    _order = 'client_idx, idx'
    # _order = 'client_idx asc'

    _sql_constraints = [
        ('idx_unique', 'unique(idx)', 'site idx already exists!'),
        ('client_site_unique', 'unique(client_id,dc)', 'site already exists!'),
    ]

    partner_id = fields.Many2one('res.partner', string="Address",
                                 domain="[('id','in',address_ids),('type','=','delivery')]")
    address_ids = fields.One2many(related='client_id.partner_id.child_ids', readonly=True)
    client_id = fields.Many2one('omixtory.client', required=True,
                                context={'default_client_id': lambda r: r.id}, ondelete="cascade",
                                states={'normal': [('readonly', True)]})
    client_idx = fields.Integer(related='client_id.idx', readonly=True, store=True)
    dc = fields.Char('Site name', required=True,
                     states={'normal': [('readonly', True)]})
    idx = fields.Integer("Site Index", default=False, required=True,
                     states={'normal': [('readonly', True)]})
    box_network_prefix = fields.Char("box_network_prefix", config=True, required=True,
                     states={'normal': [('readonly', True)]})
    arc = fields.Boolean('Uses ARC', config=True, default=False)

    host_ids = fields.One2many('omixtory.host', 'site_id', string="Hosts")
    host_ids_str = fields.Char(string='Hosts', compute='_compute_host_ids_str')
    box_ids = fields.One2many('omixtory.box', 'site_id', string="Omix box list")
    box_ids_str = fields.Char(string='Omix box list', compute='_compute_box_ids_str')
    box_id = fields.Many2one('omixtory.box', "Default Box", domain="[('site_id','=',id)]")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    @api.depends('host_ids.dc')
    def _compute_host_ids_str(self):
        for rec in self:
            rec.host_ids_str = ','.join(rec.mapped('host_ids.dc'))

    @api.depends('box_ids.dc')
    def _compute_box_ids_str(self):
        for rec in self:
            rec.box_ids_str = ','.join(rec.mapped('box_ids.dc'))

    @api.onchange('box_network_prefix')
    def _onchange_network_prefix(self):
        for rec in self.host_ids:
            rec.ip = self._change_ip(rec.ip, self.box_network_prefix)
            pass
        for rec in self.box_ids:
            rec.ip = self._change_ip(rec.ip, self.box_network_prefix)
            pass

    @staticmethod
    def _change_ip(ip, new_prefix):
        return new_prefix + '.' + ip.split('.', 4)[3]

    def get_domain(self):
        return (self.dc + '.' if self.dc != self.client_id.dc else '') + self.client_id.get_domain()
        # return "{}{}.omx".format(self.dc + '.' if self.dc != self.client_id.dc else '', self.client_id.dc)

    def _get_boxes(self):
        return self.box_ids.box_list()

    # def _get_boxes_d(self):
    #     return self.box_ids.box_list_d()

    def _get_arc(self):
        if not self.arc:
            return []
        return ['arc.' + self.get_domain()]

    # def _next_idx(self):
    #     a = self.search([]).mapped('idx')
    #     zzz = set(range(1,1000)) - set(a)
    #     return list(zzz)[0]
    #     return next_idx(self.env.cr, 'site', 'idx', 0)

    @api.onchange('idx')
    def _onchange_idx(self):
        # if self.idx and self.idx < 8128:
        self.box_network_prefix = calc_prefix(self.idx, 32)

    def _next_idx(self):
        return list(
            set(range(1, MAXIDX)) - (
                    set(self.client_id.site_ids.mapped('idx')) |
                    set(self.with_context(active_test=False).search([]).mapped('idx'))
            )
        )[0]

    @api.onchange('client_id')
    def _onchange_client(self):
        if self.client_id:
            self.idx = self._next_idx()
            if self.client_id.dc not in self.client_id.site_ids.mapped('dc'):
                self.dc = self.client_id.dc

    @api.constrains('state')
    def _validate_state(self):
        for rec in self:
            if rec.state == 'normal' and rec.client_id.state == 'draft':
                raise ValidationError('Client is draft - cant change!')

    @api.constrains('active')
    def _validate_active(self):
        for rec in self:
            if rec.active and not rec.client_id.active:
                raise ValidationError('Unarchive Client first!')

    def group(self):
        return self.client_id.dc + '_' + self.dc

    def _vars(self):
        vals = {k: self[k] for k, d in self._fields.items() if d._attrs and d._attrs['config']}
        vals.update({
            'site': self.dc if self.client_id.dc == self.dc else self.client_id.dc + '_' + self.dc,
            'site_domain': self.client_id.dc + '.omx'
            if self.client_id.dc == self.dc else self.dc + '.' + self.client_id.dc + '.omx',
            'default_box': self.box_id.name,
            'default_gateway': self.box_network_prefix + ".1",
            'ipovpn': calc_vpn_ip(self.idx, 26),
            'iparc': calc_vpn_ip(self.idx, 27)
        })
        return vals

    def _hosts(self):
        return [r.name for r in self.host_ids if r.state == 'normal']

    def _inventory(self):
        return {
                "vars": self._vars(),
                "hosts": self._hosts() + self._get_boxes()  # + self._get_boxes_d()
                + (["arc." + self.get_domain()] if self.arc else [])
            }

    @api.multi
    def inventory(self):
        return {r.group(): r._inventory() for r in self if r.state == 'normal'}

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            vals['state'] = 'draft'
        res = super(Site, self).write(vals)
        if not res:
            return res
        if 'active' in vals or 'state' in vals:
            hosts = self.env['omixtory.host'].search([('site_id', 'in', self.ids)])
            boxes = self.env['omixtory.box'].search([('site_id', 'in', self.ids)])
            if 'active' in vals and not vals['active']:
                hosts.write({'active': False})
                boxes.write({'active': False})
            if 'state' in vals:
                hosts.write({'state': vals['state']})
                boxes.write({'state': vals['state']})
        if 'arc' in vals:
            boxes = self.env['omixtory.box'].search([('site_id', 'in', self.ids)])
            for box in boxes:
                box.direct_ip = box.ip if vals['arc'] else '0.0.0.0'
        return res

    @api.model
    def create(self, vals):
        res = super(Site, self).create(vals)
        box = self.env['omixtory.box'].create({
            'site_id': res.id,
            'direct_ip': '0.0.0.0',
        })
        box._onchange_site_id()
        box._onchange_ip()
        res.box_id = box
        host = self.env['omixtory.host'].create({
            'client_id': res.client_id.id,
            'site_id': res.id,
            'dc': 'gw',
            'template_id': self.env.ref('omixtory.config_gw').id,
        })
        host.on_create()
        return res
