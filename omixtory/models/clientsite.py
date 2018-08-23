# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

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

    partner_id = fields.Many2one('res.partner', domain=[('is_company', '=', True)])
    dc = fields.Char('Client Name', required=True)
    idx = fields.Integer("Site IDX", default=lambda self: self._next_idx(), required=True)
    cloud_network_prefix = fields.Char("cloud_network_prefix", required=True)
    vpn_network_prefix = fields.Char("vpn_network_prefix", required=True)
    site_ids = fields.One2many('omixtory.site', 'client_id')
    host_ids = fields.One2many('omixtory.host', 'client_id', domain=[('site_id','=',False)])
    ad_domain = fields.Char("AD domain", config=True, required=True)
    ldap_base = fields.Char('ldap_base', config=True, required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    def _next_idx(self):
        self.env.cr.execute(_next_idx_sql.format(tab='client'))
        res = self.env.cr.fetchone()
        return res[0] if res else 1

    @api.onchange('idx')
    def _onchange_idx(self):
        if self.idx and self.idx < 8128:
            self.cloud_network_prefix = _calc_prefix(self.idx, 64)
            self.vpn_network_prefix = _calc_prefix(self.idx, 160)

    @api.onchange('dc')
    def _onchange_dc(self):
        if self.dc:
            self.ad_domain = "ad.{}.omx".format(self.dc)
            self.ldap_base = "dc=ad,dc={},dc=omx".format(self.dc)

    @api.onchange('state')
    def _onchange_state(self):
        self.site_ids.write({'state': self.state})
        self.host_ids.write({'state': self.state})

    def _vars(self):
        vars = {k: self[k] for k, d in self._fields.items() if d._attrs and d._attrs['config']}
        vars.update({
            'client': self.dc
        })
        return vars

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
    def write(self,vals):
        res = super(Client,self).write(vals)
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


class Site(models.Model):
    _name = 'omixtory.site'
    _rec_name = "dc"
    _sql_constraints = [
        ('idx_unique', 'unique(idx)', 'site idx already exists!'),
        ('client_site_unique', 'unique(client_id,dc)', 'site already exists!'),
    ]

    partner_id = fields.Many2one('res.partner', domain="[('id','in',address_ids),('type','=','delivery')]")
    address_ids = fields.One2many(related='client_id.partner_id.child_ids', readonly=True)
    client_id = fields.Many2one('omixtory.client', required=True, context={'default_client_id' : lambda r: r.id})
    dc = fields.Char('Site name', required=True)
    idx = fields.Integer("Site IDX", default=lambda self: self._next_idx(), required=True)
    box_network_prefix = fields.Char("box_network_prefix", required=True)
    host_ids = fields.One2many('omixtory.host', 'site_id')
    boxes = fields.Char("Omix box list", help="Comma separated list of boxes", default='pm1', required=True)
    default_boxname = fields.Char("Default Box Hostname", default='pm1', required=True)
    arc = fields.Boolean('Uses ARC',default=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    # lambda self: [('id', 'in', self.client_id.partner_id.child_ids.ids)]


    def _get_domain(self):
        return "{}{}.omx".format(self.dc + '.' if self.dc != self.client_id.dc else '', self.client_id.dc)

    def _get_boxes(self):
        if not self.boxes:
            return []
        return [b + '.' + self._get_domain() for b in self.boxes.split(",")]

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
        vars = {k: self[k] for k, d in self._fields.items() if d._attrs and d._attrs['config']}
        vars.update({
            'default_boxname': self.default_boxname + "." + self._get_domain()
        })
        return vars

    def _hosts(self):
        return [r.name for r in self.host_ids if r.state == 'normal']

    def _inventory(self):
        return {
                "vars": self._vars(),
                "hosts": self._hosts() + self._get_boxes() + (["arc." + self._get_domain()] if self.arc else [])
            }

    @api.multi
    def inventory(self):
        return {r.group(): r._inventory() for r in self if r.state == 'normal'}

    @api.multi
    def write(self,vals):
        res = super(Site,self).write(vals)
        if not res:
            return res
        if 'active' in vals or 'state' in vals:
            hosts = self.env['omixtory.host'].search([('site_id', 'in', self.ids)])
            if 'active' in vals and not vals['active']:
                hosts.write({'active': False})
            if 'state' in vals:
                hosts.write({'state': vals['state']})
        return res
