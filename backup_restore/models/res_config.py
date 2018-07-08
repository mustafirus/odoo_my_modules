# -*- coding: utf-8 -*-
import string
from glob import glob

from odoo import models, fields, api, _
from odoo.service.db import dump_db, exp_drop, restore_db
from odoo.exceptions import AccessError
import os
import errno
from os.path import expanduser
from odoo.http import request

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

        self.backup_name = self.backup_name.replace(' ', '_')

        with open("{}/{}.zip".format(backup_dir,self.backup_name), "wb", 0o600) as file:
            dump_db(self._cr.dbname,file)


    @api.multi
    def restore(self):
        self.ensure_one()
        if not self.env.user._is_superuser() and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("Only administrators can change the settings"))

        dbname = self._cr.dbname
        restore_name = self.restore_name
        request.session.logout()
        request.disable_db = True
        request._cr = None
        exp_drop(dbname)
        restore_db(dbname, restore_name)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/login',
            'target': 'self',
        }
