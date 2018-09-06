# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from . common import _next_idx_sql, _calc_prefix

class Site(models.Model):
    _name = 'omixtory.site'
    _rec_name = "dc"
    _sql_constraints = [
        ('idx_unique', 'unique(idx)', 'site idx already exists!'),
        ('client_site_unique', 'unique(client_id,dc)', 'site already exists!'),
    ]

    partner_id = fields.Many2one('res.partner', domain="[('id','in',address_ids),('type','=','delivery')]")
    address_ids = fields.One2many(related='client_id.partner_id.child_ids', readonly=True)
    client_id = fields.Many2one('omixtory.client', required=True,
                                context={'default_client_id': lambda r: r.id}, ondelete="cascade",
                                states={'normal': [('readonly', True)]})
    dc = fields.Char('Site name', required=True,
                     states={'normal': [('readonly', True)]})
    idx = fields.Integer("Site Index", default=lambda self: self._next_idx(), required=True,
                     states={'normal': [('readonly', True)]})
    box_network_prefix = fields.Char("box_network_prefix", required=True,
                     states={'normal': [('readonly', True)]})
    arc = fields.Boolean('Uses ARC', default=False)

    host_ids = fields.One2many('omixtory.host', 'site_id', string="Hosts")
    box_ids = fields.One2many('omixtory.box', 'site_id', string="Omix box list")
    box_id = fields.Many2one('omixtory.box', "Default Box", domain="[('site_id','=',id)]")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    def _get_domain(self):
        return "{}{}.omx".format(self.dc + '.' if self.dc != self.client_id.dc else '', self.client_id.dc)

    def _get_boxes(self):
        return self.box_ids.box_list()

    def _get_boxes_d(self):
        return self.box_ids.box_list_d()

    def _get_arc(self):
        if not self.arc:
            return []
        return ['arc.' + self._get_domain()]

    def _next_idx(self):
        self.env.cr.execute(_next_idx_sql.format(tab='site'))
        res = self.env.cr.fetchone()
        return res[0] if res else 1

    @api.onchange('idx')
    def _onchange_idx(self):
        if self.idx and self.idx < 8128:
            self.box_network_prefix = _calc_prefix(self.idx, 32)

    @api.onchange('client_id')
    def _onchange_client(self):
        if self.client_id:
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
            'default_box': self.box_id.name
        })
        return vals

    def _hosts(self):
        return [r.name for r in self.host_ids if r.state == 'normal']

    def _inventory(self):
        return {
                "vars": self._vars(),
                "hosts": self._hosts() + self._get_boxes() + self._get_boxes_d()
                + (["arc." + self._get_domain()] if self.arc else [])
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
        return res
