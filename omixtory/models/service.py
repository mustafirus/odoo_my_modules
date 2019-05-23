# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HostTemplate(models.Model):
    _name = "omixtory.host.template"
    _sql_constraints = [
        ('model_unique', 'unique(model)', 'model already exists!'),
    ]

    name = fields.Char()  # Description xxx
    model = fields.Char()  # model _name: omixtory.config.xxx
    tabl = fields.Char()  # model _table: omixtory.config.xxx

    siteonly = fields.Boolean()
    host = fields.Char()
    ip_suffix = fields.Integer()
    host_ids = fields.One2many('omixtory.host', 'template_id')
    active = fields.Boolean(default=True)

    @api.model
    def install(self):
        models = self.env['ir.model'].search([('model', 'like', 'omixtory.config.%')], order='id') #sudo().
        imd = self.env['ir.model.data']  # .sudo()
        imd_data_list = []

        for model in models:
            conf = self.env[model.model]
            vals = {
                'name': model.name,
                'model': model.model,
                'tabl': conf._table,
                'siteonly': conf.siteonly,
                'host': conf.host,
                'ip_suffix': conf.ip_suffix,
            }
            t = self.search([('model', '=', model.model)])
            if t:
                t.write(vals)
            else:
                t = self.create(vals)
            imd_data_list.append({
                'xml_id': 'omixtory.config_' + t.name,
                'record': t,
                'noupdate': False
            })
        # [{'values': {'description': 'Omix inventory', 'sequence': 15, 'name': 'Omixtory1'},
        # 'xml_id': 'omixtory.module_category_omixtory',
        # 'record': ir.module.category(74, ),
        # 'noupdate': False}]
        imd._update_xmlids(imd_data_list, True)
        for template in self.search([]):
            if not self.env['ir.model'].search_count([('model', '=', template.model)]):
                template.unlink()

    def _hosts(self):
        return [r.name for r in self.host_ids if r.state == 'normal']

    def _vars(self):
        return {k: self[k] for k, d in self._fields.items() if d._attrs and d._attrs['inventory']}

    def _inventory(self):
        return {
                "vars": self._vars(),
                "hosts": self._hosts()
            }

    @api.multi
    def inventory(self):
        inv = {r.name: r._inventory() for r in self}
        sites = self.env['omixtory.site'].search([])
        boxes = []
        boxes_d = []
        arcs = []
        for s in sites:
            boxes += s._get_boxes()
            boxes_d += s._get_boxes_d()
            if s.arc:
                arcs += ["arc." + s.get_domain()]
        inv.update({
            "pmd": {'hosts': boxes_d},
            "pm": {'hosts': boxes},
            "arc": {'hosts': arcs},
        })
        return inv


class ConfigGw(models.Model):
    _name = 'omixtory.config.gw'
    _description = "gw"
    name = fields.Char('FQDN', readonly=True)

    siteonly = True
    host = 'gw'
    ip_suffix = 1

    dhcp = fields.Boolean("Enable DHCP", inventory=True)


# class ConfigProxy(models.Model):
#     _name = 'omixtory.config.proxy'
#     _description = "proxy"
#     name = fields.Char('FQDN', readonly=True)
#
#     siteonly = False
#     host = 'proxy'
#     ip_suffix = 2


class ConfigMail(models.Model):
    _name = 'omixtory.config.mail'
    _description = "mail"
    name = fields.Char('FQDN', readonly=True)

    siteonly = False
    host = 'mail'
    ip_suffix = 3

    roundcube = fields.Boolean("Install roundcube", inventory=True)


# class ConfigWp(models.Model):
#     _name = 'omixtory.config.wp'
#     _description = "wp"
#     name = fields.Char('FQDN', readonly=True)
#
#     siteonly = False
#     host = 'wp'
#     ip_suffix = 4
#
#     # list of proxy sites
#

# class ConfigOdoo(models.Model):
#     _name = 'omixtory.config.odoo'
#     _description = "odoo"
#     name = fields.Char('FQDN', readonly=True)
#
#     siteonly = False
#     host = 'odoo'
#     ip_suffix = 5


class ConfigDc(models.Model):
    _name = 'omixtory.config.dc'
    _description = "dc"
    name = fields.Char('FQDN', readonly=True)

    siteonly = True
    host = 'dc1'
    ip_suffix = 8


class ConfigFiles(models.Model):
    _name = 'omixtory.config.files'
    _description = "files"
    name = fields.Char('FQDN', readonly=True)

    siteonly = False
    host = 'files'
    ip_suffix = 9
