# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from odoo import http
from os.path import expanduser
from odoo.service.db import exp_drop, restore_db
from odoo.http import request

class backup_restore(http.Controller):
    @http.route('/backup_restore/restore/<dbname>/<restore_name>', auth='none')
    def backup_restore(self, dbname, restore_name, **kw):
        backup_dir = expanduser("~/user_backups/%s" % dbname)
        restore_name = "%s/%s.zip" % (backup_dir, restore_name)
        request.session.logout()
        request.disable_db = True
        request._cr = None
        exp_drop(dbname)
        restore_db(dbname, restore_name)
        return http.local_redirect('/web/database/manager')
        # return redirect("/")
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': '/',
        #     'target': 'self',
        # }

