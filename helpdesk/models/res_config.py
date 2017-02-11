import string
from glob import glob

from odoo import models, fields, api, _
from odoo.service.db import dump_db, exp_drop, restore_db
from odoo.exceptions import AccessError
import os
import errno
import odoo
from os.path import expanduser

class HelpdeskConfig(models.TransientModel):
    _name = 'helpdesk.config.settings'
    _inherit = 'res.config.settings'

    # default_team_id = fields.Many2one("helpdesk.team","Default team", help="(alpha team, 1st line support)")
    default_name = fields.Char('Default ticket name', default_model='helpdesk.ticket')
    module_helpdesk_website = fields.Boolean("Publish on website", help='Installs module helpdesk_website')

    # @api.model
    # def get_default_team_id(self, fields):
    #     default_team_id = False
    #     if 'default_team_id' in fields:
    #         default_team_id = self.env['ir.values'].get_default('helpdesk.ticket', 'team_id',
    #                                                              company_id=self.env.user.company_id.id)
    #     return {
    #         'default_team_id': default_team_id
    #     }
    #
    # @api.multi
    # def set_default_team_id(self):
    #     for wizard in self:
    #         ir_values = self.env['ir.values']
    #         if self.user_has_groups('base.group_configuration'):
    #             ir_values = ir_values.sudo()
    #         ir_values.set_default('helpdesk.ticket', 'team_id', wizard.default_team_id.id,
    #                               company_id=self.env.user.company_id.id)

