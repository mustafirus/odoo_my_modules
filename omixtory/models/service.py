# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Service(models.Model):
    _name = 'omixtory.service'

    name = fields.Char()
    host_id = fields.Many2one('omixtory.host')
    client_id = fields.Many2one(related='host_id.client_id', readonly=True)
    config = fields.Reference(string='Config', selection=[])

    @api.multi
    def open_config(self):
        # config_model, config_id = self.config.split(',')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.config._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.config.id,
            'views': [(False, 'form')],
            'target': 'new',
             }

    # @api.multi
    # def write(self, vals):
    #     return super(Service, self).write(vals)

    # @api.model
    # def _reference_models(self):
    #     models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')])
    #     zzz =  [(model.model, model.name)
    #             for model in models
    #             if model.model.startswith('omixtory.config.')]
    #     return zzz
    #

class ServiceGw(models.Model):
    _name = 'omixtory.config.gw'
    _description = "gw"

    siteonly = True
    host = 'gw'
    ip_suffix = 1

    dhcp = fields.Boolean("Enable DHCP")


class ServiceDc(models.Model):
    _name = 'omixtory.config.dc'
    _description = "dc"

    siteonly = False
    host = 'dc1'
    ip_suffix = 8

