from odoo import models, fields, api
from odoo.exceptions import UserError


class ServiceCreate(models.TransientModel):
    _name = "omixtory.service.create"

    client_id = fields.Many2one('omixtory.client', required=True)
    site_id = fields.Many2one('omixtory.site', domain="[('client_id','=',client_id)]")
    config = fields.Many2one('omixtory.service.template', order='id', required=True,
                              domain="['|',('siteonly','=',site_id),('siteonly','=',False)]")
    location = fields.Selection([('box', 'Box'), ('cloud', 'Cloud')])

    @api.onchange('client_id')
    def _onchange_client(self):
        self.site_id = False
        self.config = False

    @api.onchange('site_id')
    def _onchange_site(self):
        self.location = 'box' if self.site_id else 'cloud'
        self.config = False

    @api.multi
    def create_service(self):
        self.ensure_one()
        if not self.client_id or not self.config:
            raise UserError('Incorrect data!')

        ip_prefix = self.site_id.box_network_prefix if self.site_id \
            else self.client_id.cloud_network_prefix
        fqdn = ".".join((t for t in (self.config.host,
                                     self.site_id.dc if self.config.siteonly else False,
                                     self.client_id.dc,
                                     "omx") if t))
        host = self.env['omixtory.host'].search([('name', '=', fqdn)])
        if not host:
            host = self.env['omixtory.host'].create({
                'name': fqdn,
                'ip': ip_prefix + "." + str(self.config.ip_suffix),
                'vmid': str(100 + self.config.ip_suffix if self.config.siteonly
                       else 1000000 + self.client_id.idx*100 + self.config.ip_suffix),
                'site_id': self.site_id.id,
                'client_id': self.client_id.id,
            })
        service_name = ' '.join((t for t in (self.client_id.dc,
                                     self.site_id.dc if self.config.siteonly else False,
                                     self.config.name) if t))
        service = self.env['omixtory.service'].search([('name', '=', service_name)])
        if service:
            raise UserError('Service "{}" exists!'.format(service_name))
        config_id = self.env[self.config.model].create([]).id
        service = self.env['omixtory.service'].create({
            'name': service_name,
            'host_id': host.id,
            'config': "{},{}".format(self.config.model, config_id),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self.config.model,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': config_id,
            'views': [(False, 'form')],
            'target': 'new',
             }
