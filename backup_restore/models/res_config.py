# -*- coding: utf-8 -*-
import string
from glob import glob

from odoo import models, fields, api, _
from odoo.service.db import dump_db, exp_drop, restore_db
from odoo.exceptions import AccessError
import os
import errno
import odoo
from os.path import expanduser

backup_dir = "unknown"

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

class BackupRestore(models.TransientModel):
    _name = 'backup_restore.config.settings'
    _inherit = 'res.config.settings'


    def __init__(self,pool,cr):
        global backup_dir
        backup_dir = expanduser("~/user_backups/%s" % cr.dbname)
        make_sure_path_exists(backup_dir)
        super(BackupRestore,self).__init__(pool,cr)

    backup_name = fields.Char("Backup name")
    restore_name = fields.Selection(selection='get_backup_list')

    def get_backup_list(self):
        path = "%s/*.zip" % backup_dir
        ret = ()
        for file in glob(path):
            name = os.path.splitext(os.path.basename(file))[0]
            ret += ((file, name),)

        return ret

    @api.multi
    def backup(self):
        self.ensure_one()
        if not self.env.user._is_superuser() and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("Only administrators can change the settings"))

        if not self.backup_name:
            return

        self.backup_name = string.replace(self.backup_name,' ', '_')

        file = open("%s/%s.zip" % (backup_dir,self.backup_name),"w", 0600)
        dump_db(self._cr.dbname,file)
        file.close()


    @api.multi
    def restore(self):
        self.ensure_one()
        if not self.env.user._is_superuser() and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("Only administrators can change the settings"))

        dbname = self._cr.dbname
        restore_name = self.restore_name

        exp_drop(dbname)
        restore_db(dbname, restore_name)



#        restore_db(db, dump_file, copy=False)
    # @api.model
    # def get_default_use_svami(self, fields):
    #     use_svami = self.env["ir.config_parameter"].get_param("svami.use_svami", default=False)
    #     return {'use_svami': use_svami}
    #
    # @api.one
    # def set_use_svami(self):
    #     use_svami = self.use_svami
    #     alias_domain = self.alias_domain
    #     alias_domain_old = self.env['ir.config_parameter'].get_param("svami.use_svami")
    #     mail_server= self.env['ir.mail_server'].sudo().search([('name', '=', 'svami')])
    #     fetchmail_server= self.env['fetchmail.server'].sudo().search([('name', '=', 'svami')])
    #     if not use_svami or not is_alias_on_svami(alias_domain):
    #         if len(mail_server) > 0:
    #             mail_server.unlink()
    #             fetchmail_server.unlink()
    #         self.env['ir.config_parameter'].set_param("svami.use_svami", False)
    #         return
    #     if (alias_domain !=  alias_domain_old and len(mail_server) > 0) or len(mail_server) > 1:
    #         mail_server.unlink()
    #         fetchmail_server.unlink()
    #
    #     mail_server.create(
    #         {'name': "svami", 'smtp_host': "mail.svami.in.ua", 'smtp_port': "587",
    #          'smtp_encryption': "starttls"}
    #     )
    #     fetchmail_server.create(
    #         {'name': "svami", 'server': "mail.svami.in.ua", 'port': "993",
    #          'type': 'imap', 'is_ssl': True}
    #     )
    #     self.env['ir.config_parameter'].set_param("svami.use_svami", alias_domain)


    # @api.depends('use_svami')
    # def onchange_use_svami(self):
    #     a = self.use_svami
    #     if self.use_svami:
    #         return {
    #             'warning': {
    #                 'title': _('Warning!'),
    #                 'message': _('Check creditials in svami outgoing and incoming servers settings \n'),
    #             }
    #         }


    #    @api.onchange('alias_domain')
#    def onchange_svami(self):
#        c = self.alias_domain_changed
#        if self.use_svami:
#            if self.alias_domain != self.env['ir.config_parameter'].get_param("mail.catchall.domain"):
#                self.alias_domain_changed = True
#        c = self.alias_domain_changed
#        a=1

