# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class HostTemplate(models.Model):
    _name = "omixtory.host.template"
    _sql_constraints = [
        ('model_unique', 'unique(model)', 'model already exists!'),
    ]

    name = fields.Char()  # Description xxx
    model = fields.Char() #model _name: omixtory.config.xxx

    siteonly = fields.Boolean()
    host = fields.Char()
    ip_suffix = fields.Integer()
    host_ids = fields.One2many('omixtory.host', 'template_id')

    @api.model
    def install(self):
        # self.search([]).unlink()
        models = self.env['ir.model'].sudo().search([('model', 'like', 'omixtory.config.%')], order='id')
        for model in models:
            conf = self.env[model.model]
            vals = {
                'name': model.name,
                'model': model.model,
                'siteonly': conf.siteonly,
                'host': conf.host,
                'ip_suffix': conf.ip_suffix,
            }
            t = self.search([('model', '=', model.model)])
            if t:
                t.write(vals)
            else:
                self.create()

    def _hosts(self):
        return [r.name for r in self.host_ids]

    def _vars(self):
        return {k: self[k] for k, d in self._fields.items() if d._attrs and d._attrs['config']}

    def _inventory(self):
        return {
                "vars": self._vars(),
                "hosts": self._hosts()
            }

    @api.multi
    def inventory(self):
        return { r.name: r._inventory() for r in self }


class Host(models.Model):
    _name = 'omixtory.host'

    name = fields.Char('FQDN')
    client_id = fields.Many2one('omixtory.client', required=True)
    site_id = fields.Many2one('omixtory.site')
    template_id = fields.Many2one('omixtory.host.template', order='id', required=True, store=True,
                              domain="['|',('siteonly','=',site_id),('siteonly','=',False)]")
    location = fields.Selection([('box', 'Box'), ('cloud', 'Cloud')], compute='_compute_location')
    ip = fields.Char('IP')
    vmid = fields.Char("VMID")
    config = fields.Reference(string='Config', selection=[])
    state = fields.Selection({
        ('draft','Draft')
        ('config', 'Config')
        ('aplied', 'Aplied')
    })

    @api.onchange('client_id')
    def _onchange_client(self):
        self.site_id = False
        self.template_id = False

    @api.onchange('site_id')
    def _onchange_site(self):
        self.template_id = False

    @api.depends('site_id')
    def _compute_location(self):
        self.location = 'box' if self.site_id else 'cloud'

    @api.multi
    def open_config(self):
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
    def unlink(self):
        for rec in self:
            if rec.config:
                rec.config.unlink()
        return super(Host,self).unlink()

    @api.model
    def create(self,vals):
        if not 'template_id' in vals:
            raise UserError('Template is required!')

        client_id = self.env['omixtory.client'].search([('id', '=', vals['client_id'])])
        site_id = self.env['omixtory.site'].search([('id', '=', vals['site_id'])]) \
            if 'site_id' in vals else False
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
                'site_id': site_id.id,
                'client_id': client_id.id,
                'config': "{},{}".format(template_id.model, self.env[template_id.model].create({'name': fqdn}).id),
        })

        return super(Host,self).create(vals)

    @api.multi
    def hostvars(self):
        return { r.name: r._hostvars() for r in self }

    def _hostvars(self):
        return {k: self.config[k] for k,d in self.config._fields.items() if d._attrs and d._attrs['config']}


class ConfigGw(models.Model):
    _name = 'omixtory.config.gw'
    _description = "gw"

    siteonly = True
    host = 'gw'
    ip_suffix = 1

    name = fields.Char('FQDN', readonly=True)
    dhcp = fields.Boolean("Enable DHCP", config=True)


class ConfigProxy(models.Model):
    _name = 'omixtory.config.proxy'
    _description = "proxy"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'proxy'
    ip_suffix = 2

    name = fields.Char('FQDN', readonly=True)


class ConfigMail(models.Model):
    _name = 'omixtory.config.mail'
    _description = "mail"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'mail'
    ip_suffix = 3

    name = fields.Char('FQDN', readonly=True)

    roundcube = fields.Boolean("Install roundcube", config=True)


class ConfigWp(models.Model):
    _name = 'omixtory.config.wp'
    _description = "wp"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'wp'
    ip_suffix = 4

    name = fields.Char('FQDN', readonly=True)

    # list of proxy sites


class ConfigOdoo(models.Model):
    _name = 'omixtory.config.odoo'
    _description = "odoo"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'odoo'
    ip_suffix = 5

    name = fields.Char('FQDN', readonly=True)


class ConfigDc(models.Model):
    _name = 'omixtory.config.dc'
    _description = "dc"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'dc1'
    ip_suffix = 8

    name = fields.Char('FQDN', readonly=True)


class ConfigFiles(models.Model):
    _name = 'omixtory.config.files'
    _description = "files"
    name = fields.Char('FQDN')

    siteonly = False
    host = 'files'
    ip_suffix = 9

    name = fields.Char('FQDN', readonly=True)

