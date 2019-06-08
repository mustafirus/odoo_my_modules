# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Host(models.Model):
    _name = 'omixtory.host'

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'host name already exists!'),
    ]

    # @api.model
    # def _get_domain(self):
    #     gw = self.env.ref('omixtory.config_gw')
    #     all = gw.search([])
    #     if self.site_id:
    #         ids = (all - gw).ids
    #     else:
    #         ids = all.ids
    #     return [('id', 'in', ids)]

    name = fields.Char('FQDN', compute='_compute_name', store=True)
    dc = fields.Char('Hostname', required=True)
    domain = fields.Char('Domain', compute='_compute_domain', required=True)
    client_id = fields.Many2one('omixtory.client', required=True, ondelete="cascade",
                     states={'normal': [('readonly', True)]})
    site_id = fields.Many2one('omixtory.site', domain="[('client_id', '=', client_id)]", ondelete="cascade",
                     states={'normal': [('readonly', True)]})
    template_id = fields.Many2one('omixtory.host.template', order='id', required=True, store=True,
                                  # domain="['|',('siteonly','=',site_id),('siteonly','=',False)]",
                                  domain="[('host','!=','gw')]",
                     states={'normal': [('readonly', True)]})
    location = fields.Selection([('box', 'Box'), ('cloud', 'Cloud')], compute='_compute_location')

    ip = fields.Char('IP', inventory=True,
                     states={'normal': [('readonly', True)]})
    vmid = fields.Char("VMID", inventory=True,
                     states={'normal': [('readonly', True)]})
    config = fields.Reference(string='Config', selection=[])

    ssh_url = fields.Char('ssh', compute='_compute_ssh_url')

    # cores = fields.Selection([('512','512M')])
    # mem = fields.Selection([('512','512M')])
    # disk = fields.Selection([('512','512M')])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    @api.depends('site_id.dc', 'client_id.dc', 'template_id')
    def _compute_domain(self):
        for rec in self:
            if not rec.template_id or not rec.client_id:
                return
            if rec.template_id.siteonly:
                if rec.site_id:
                    rec.domain = rec.site_id.get_domain()
                else:
                    rec.domain =  'ssc.' + rec.client_id.get_domain()
            else:
                rec.domain = rec.client_id.get_domain()

    @api.depends('dc', 'domain')
    def _compute_name(self):
        for rec in self:
            if rec.dc:
                rec.name = rec.dc + '.' + rec.domain
            pass

    @api.depends('site_id')
    def _compute_location(self):
        self.location = 'box' if self.site_id else 'cloud'

    @api.multi
    def _compute_ssh_url(self):
        for rec in self:
            rec.ssh_url = 'ssh://root@' + rec.name if rec.name else ''


    @api.onchange('client_id','template_id')
    def _onchange_client(self):
        if self.site_id and self.site_id.client_id != self.client_id:
            self.site_id = False
        if self.template_id.siteonly:
            if self.site_id:
                vmid = 100 + self.template_id.ip_suffix
            else:
                vmid = 80000 + self.client_id.idx
        else:
            vmid = 7000000 + self.client_id.idx * 100 + self.template_id.ip_suffix
        self.vmid = str(vmid)

    @api.onchange('site_id', 'template_id')
    def _onchange_site_template(self):
        ip_prefix = self.site_id.box_network_prefix if self.site_id \
            else self.client_id.cloud_network_prefix
        if ip_prefix and self.template_id:
            self.ip = ip_prefix + "." + str(self.template_id.ip_suffix)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        self.dc = self.template_id.host

    @api.constrains('state','active')
    def _validate_state_active(self):
        for rec in self:
            rec._validate_state_active_one()

    def _validate_state_active_one(self):
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

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.config:
    #             rec.config.unlink()
    #     return super(Host, self).unlink()

    @api.multi
    def on_create(self):
        self.ensure_one()
        self._onchange_client()
        self._onchange_site_template()


    @api.model_create_single
    def create(self, vals):
        if 'template_id' not in vals:
            raise UserError('Template is required!')

        client_id = self.env['omixtory.client'].search([('id', '=', vals['client_id'])])
        site_id = self.env['omixtory.site'].search([('id', '=', vals['site_id'])])  # if 'site_id' in vals else False
        template_id = self.env['omixtory.host.template'].search([('id', '=', vals['template_id'])])

        # ip_prefix = site_id.box_network_prefix if site_id \
        #     else client_id.cloud_network_prefix
        # fqdn = ".".join((t for t in (template_id.host,
        #                              site_id.dc if template_id.siteonly and site_id.dc != client_id.dc else False,
        #                              client_id.dc,
        #                              "omx") if t))

        # fqdn = vals['name']
        # host = self.search([('name', '=', vals['name'])])
        # if host:
        #     return host

#         vals.update({
#                 # 'name': fqdn,
#                 # 'ip': ip_prefix + "." + str(template_id.ip_suffix),
#                 # 'vmid': str(100 + template_id.ip_suffix if template_id.siteonly
#                 #        else 1000000 + client_id.idx*100 + template_id.ip_suffix),
# #                'site_id': site_id.id,
# #                'client_id': client_id.id,
#                 'config': "{},{}".format(template_id.model, self.env[template_id.model].create({'name': fqdn}).id),
#         })
        # res.config = "{},{}".format(template_id.model, self.env[template_id.model].create({'name': res.name}).id),

        res = super(Host, self).create(vals)
        config = self.env[res.template_id.model].create({'name': res.name})
        res.config = "{},{}".format(config._name, config.id)
        res._ensure_vlanid()
        return res

    @api.multi
    def open_config(self):
        self.ensure_one()
        if not self.config:
            raise UserError('Config not found. DB Error!')
        return {
            'name': 'Config',
            'type': 'ir.actions.act_window',
            'res_model': self.config._name,
            'view_mode': 'form',
            'view_type': 'tree',
            'res_id': self.config.id,
            'views': [(False, 'form')],
            'context': {
                'create': False
            },
            'target': 'new',
        }

    @api.multi
    def open_ssh(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': 'ssh://root@' + self.name,
            # 'target': 'new',
        }

    def _ensure_vlanid(self):
        if not self.site_id and self.client_id:
            self.client_id.ensure_vlanid()

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            vals['state'] = 'draft'
        res = super(Host, self).write(vals)
        for rec in self:
            rec._ensure_vlanid()
        return res

    @api.multi
    def hostvars(self):
        return {r.name: r._hostvars() for r in self if r.state == 'normal'}

    def _hostvars(self):
        vars = {k: self.config[k] for k,d in self.config._fields.items() if d._attrs and d._attrs.get('inventory')}
        vars.update({k: self[k] for k,d in self._fields.items() if d._attrs and d._attrs.get('inventory')})
        return vars

