# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Host(models.Model):
    _name = 'omixtory.host'

    name = fields.Char('FQDN', required=True)
    client_id = fields.Many2one('omixtory.client', required=True, ondelete="cascade",
                     states={'normal': [('readonly', True)]})
    site_id = fields.Many2one('omixtory.site', domain="[('client_id', '=', client_id)]", ondelete="cascade",
                     states={'normal': [('readonly', True)]})
    template_id = fields.Many2one('omixtory.host.template', order='id', required=True, store=True,
                                  domain="['|',('siteonly','=',site_id),('siteonly','=',False)]",
                     states={'normal': [('readonly', True)]})
    location = fields.Selection([('box', 'Box'), ('cloud', 'Cloud')], compute='_compute_location')

    ip = fields.Char('IP', inventory=True,
                     states={'normal': [('readonly', True)]})
    vmid = fields.Char("VMID", inventory=True,
                     states={'normal': [('readonly', True)]})
    config = fields.Reference(string='Config', selection=[])

    ssh_url = fields.Char('ssh', compute='_compute_ssh_url')

    cores = fields.Selection([('512','512M')])
    mem = fields.Selection([('512','512M')])
    disk = fields.Selection([('512','512M')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    @api.onchange('client_id')
    def _onchange_client(self):
        if self.site_id and self.site_id.client_id != self.client_id:
            self.site_id = False
        # self.template_id = False

    # @api.onchange('site_id')
    # def _onchange_site(self):
    #     self.template_id = False

    @api.constrains('state','active')
    def _validate_state_active(self):
        if self.state == 'normal':
            if self.client_id.state == 'draft':
                raise ValidationError('Client is draft - cant change!')
            if self.site_id.state == 'draft':
                raise ValidationError('Site is draft - cant change!')
        if self.active:
            if not self.client_id.active:
                raise ValidationError('Unarchive Client first!')
            if self.site_id and not self.site_id.active:
                raise ValidationError('Unarchive Site first!')

    @api.depends('site_id')
    def _compute_location(self):
        self.location = 'box' if self.site_id else 'cloud'

    @api.multi
    def _compute_ssh_url(self):
        for rec in self:
            rec.ssh_url = 'ssh://root@' + rec.name if rec.name else ''

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.config:
    #             rec.config.unlink()
    #     return super(Host, self).unlink()

    @api.model
    def create(self, vals):
        if 'template_id' not in vals:
            raise UserError('Template is required!')

        client_id = self.env['omixtory.client'].search([('id', '=', vals['client_id'])])
        site_id = self.env['omixtory.site'].search([('id', '=', vals['site_id'])])  # if 'site_id' in vals else False
        template_id = self.env['omixtory.host.template'].search([('id', '=', vals['template_id'])])

        ip_prefix = site_id.box_network_prefix if site_id \
            else client_id.cloud_network_prefix
        fqdn = ".".join((t for t in (template_id.host,
                                     site_id.dc if template_id.siteonly and site_id.dc != client_id.dc else False,
                                     client_id.dc,
                                     "omx") if t))
        host = self.env['omixtory.host'].search([('name', '=', fqdn)])
        if host:
            return host

        vals.update({
                'name': fqdn,
                'ip': ip_prefix + "." + str(template_id.ip_suffix),
                'vmid': str(100 + template_id.ip_suffix if template_id.siteonly
                       else 1000000 + client_id.idx*100 + template_id.ip_suffix),
#                'site_id': site_id.id,
#                'client_id': client_id.id,
                'config': "{},{}".format(template_id.model, self.env[template_id.model].create({'name': fqdn}).id),
        })

        return super(Host, self).create(vals)

    @api.multi
    def hostvars(self):
        return {r.name: r._hostvars() for r in self if r.state == 'normal'}

    def _hostvars(self):
        vars = {k: self.config[k] for k,d in self.config._fields.items() if d._attrs and d._attrs.get('inventory')}
        vars.update({k: self[k] for k,d in self._fields.items() if d._attrs and d._attrs.get('inventory')})
        return vars

    @api.multi
    def open_config(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.config._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.config.id,
            'views': [(False, 'form')],
            # 'target': 'new',
             }

    @api.multi
    def open_ssh(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': 'ssh://root@' + self.name,
            # 'target': 'new',
             }

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            vals['state'] = 'draft'
        return super(Host, self).write(vals)
