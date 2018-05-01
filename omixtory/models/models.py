# -*- coding: utf-8 -*-

from odoo import models, fields, api




class ServiceType(models.Model):
    _name = 'omixtory.service.type'

    name = fields.Char('Service Type Name')
    service_idx = fields.Integer("Service IDX")
    config_model = fields.Char("Config Model")


class Site(models.Model):
    _name = 'omixtory.site'

    partner_id = fields.Many2one('res.partner')
    # client_name = fields.Char('Client Name',related='partner_id.omix_name', required=True)
    site_name = fields.Char('Site Name')
    site_idx = fields.Integer("Site IDX")
    parent_site_id = fields.Many2one('omixtory.site')
    box_network_prefix = fields.Char("box_network_prefix")
    cloud_network_prefix = fields.Char("cloud_network_prefix")
    vpn_network_prefix = fields.Char("vpn_network_prefix")
    box_gw_lan_dhcpd = fields.Boolean("DHCP Server")
    ldap_base = fields.Char("ldap_base")
    default_boxname = fields.Char("default_boxname")

    @staticmethod
    def _calc_prefix(client_id, base):
        n3 = int((client_id - 1) / 254) + base
        n2 = (client_id - 1) % 254 + 1
        return "10.{}.{}".format(n3, n2)

    @api.onchange('site_idx')
    def _onchange_site_idx(self):
        if self.site_idx < 8128:
            self.box_network_prefix = self._calc_prefix(self.client_id, 32)
            self.cloud_network_prefix = self._calc_prefix(self.client_id, 64)
            self.vpn_network_prefix = self._calc_prefix(self.client_id, 160)


class Service(models.Model):
    _name = 'omixtory.service'

    service_type_id = fields.Many2one('omixtory.service.type')
    service_type_name = fields.Char("Config Model", related='service_type_id.name', readonly=True)
    host_id = fields.Many2one('omixtory.host')
    config_idx = fields.Integer(string='Config ID', help="ID of the config record in the database", readonly=True)
    config = fields.Char(string='Reference', compute='_compute_reference', readonly=True, store=False)

    @api.depends('service_type_name', 'config_id')
    def _compute_config(self):
        for rec in self:
            if rec.config_model and rec.config_id:
                rec.config = "omixtory.{},{}".format(rec.service_type_name, rec.config_idx)


class Host(models.Model):
    _name = 'omixtory.host'

    name = fields.Char('FQDN')
    ip = fields.Char('IP')
    vmid = fields.Integer("VMID")
    site_id = fields.Many2one('omixtory.site')
    service_ids = fields.One2many('omixtory.service', 'host_id', 'Services')

