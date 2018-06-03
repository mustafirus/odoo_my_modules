# -*- coding: utf-8 -*-
from time import gmtime,localtime, mktime
import datetime


from odoo import models, fields, api
import json
import urllib2
import logging
import werkzeug.urls

from odoo.exceptions import UserError
from slot_machine_counters.rrd import get_data_rrd, GAMBLING_ENDPOINT

_logger = logging.getLogger(__name__)

def get_now():
    return fields.datetime.now().replace(second=0, microsecond=0).strftime(fields.DATETIME_FORMAT)


class Hall(models.Model):
    _name = 'slot_machine_counters.hall'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Slot Machines Hall'

    name = fields.Char('Name of hall')
    description = fields.Text('Description')
    hub_sn = fields.Char("Hub SN", readonly=False,
                         track_visibility='onchange',
                         states={'running': [('readonly', True)]})
    phone = fields.Char("Phone of admin")
    #deprecated
    hub_sim = fields.Char("Hub SIM")
    AlarmSms = fields.Boolean("Sms Alarm")
    AlarmPhone1 = fields.Char("Alarm Phone 1")
    AlarmPhone2 = fields.Char("Alarm Phone 2")
    gpslat = fields.Float("Geo Lat")
    gpslng = fields.Float("Geo Long")
    #deprecated
    slot_ids = fields.One2many("slot_machine_counters.slot","hall_id","Slots",
                               track_visibility='onchange',
                               readonly=False, states={'running': [('readonly', True)]})
    state = fields.Selection([
        ('stopped', 'Stopped'),
        ('running', 'Running'),
        ], string='Status', index=True, readonly=True, default='stopped',
        track_visibility='always', copy=False)
    active = fields.Boolean('Active?', default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


    def get_info(self):
        url = GAMBLING_ENDPOINT + '/hubinfo?'
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        reqargs = werkzeug.url_encode({
            'hubid': fields.Datetime.from_string(self.hub_sn),
        })
        try:
            req = urllib2.Request(url + reqargs, None, headers)
            content = urllib2.urlopen(req, timeout=200).read()
        except urllib2.HTTPError:
            raise
        content = json.loads(content)
        err = content.get('error')
        if err:
            e = urllib2.HTTPError(req.get_full_url(), 999, err, headers, None)
            raise e
        self.write({
            'gpslat': content.get('gpslat'),
            'gpslng': content.get('gpslng'),
        })

    def shot(self):
        self.ensure_one()
        slotshot = self.env['slot_machine_counters.slotshot']
        slotshot.shot(self)
        pass

    def _set_config(self):
        url = GAMBLING_ENDPOINT + '/hubconfig'

        data = json.dumps({
            'hubid': self.hub_sn,
            'name': self.name,
            'AlarmSms':    self.AlarmSms,
            'AlarmPhone1': self.AlarmPhone1,
            'AlarmPhone2': self.AlarmPhone2,
            'slots': self.slot_ids.get_sns()
        })

        try:
            req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
            content = urllib2.urlopen(req, timeout=200).read()
        except urllib2.HTTPError:
            raise
        content = json.loads(content)
        err = content.get('error')
        if err:
            e = urllib2.HTTPError(req.get_full_url(), 999, err, None, None)
            raise e

    @api.multi
    def write(self, vals):
        self.ensure_one()
        if 'active' in vals:
            if self.state == 'running':
                del vals['active']

        if 'slot_ids' in vals:
            for i in range(0,len(vals['slot_ids'])):
                if vals['slot_ids'][i][0] == 2:
                    vals['slot_ids'][i][0] = 3
        # for i in range(0, len(vals['slot_conf_ids'])):
        #     if vals['slot_ids'][i][0] == 4:
        #         del vals['slot_ids'][i]
        ret = super(Hall, self).write(vals)
        # self._set_config()
        return ret

    @api.onchange('slot_ids')
    def _onchange_slot_ids(self):
        pass


class Slot(models.Model):
    _name = 'slot_machine_counters.slot'
    _rec_name = 'dev_sn'

    # name = fields.Char("Name", compute='_compute_name', readonly=True, store=True)
    index = fields.Integer("Index")
    dev_sn = fields.Char("SN Mega")
    slot_sn = fields.Char("SN Slot")
    type = fields.Char("Game type")
    boardrate  = fields.Integer("Board Rate", default=1)
    denom      = fields.Monetary("Denomenation")
    denomenation = fields.Monetary("Denomenation",compute='_compute_denomenation', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall", ondelete='set null')
    maintshot_id = fields.Many2one('slot_machine_counters.maintshot.line', string='Maintenance Slotshot')
    active = fields.Boolean('Active?', default=True)

    @api.multi
    def unlink(self):
        return super(Slot,self).unlink()


    @api.depends('boardrate','denom')
    def _compute_denomenation(self):
        for rec in self:
            rec.denomenation = (rec.denom * rec.boardrate)

    @api.multi
    def get_sns(self):
        sns = list()
        for rec in self:
            sns.append(rec.dev_sn)
        return sns

    @api.multi
    def write(self, vals):
        self.ensure_one()
        if 'active' in vals:
            if self.hall_id:
                del vals['active']

        ret = super(Slot, self).write(vals)
        return ret


    @api.multi
    def repair_begin(self):
#        slotline = self.env['slot_machine_counters.maintshot.line']
#        rrd = get_data_rrd(self.dev_sn)
        date_beg = get_now()
        rrd = get_data_rrd(self.dev_sn, date_beg, date_beg)
        iin_beg = rrd['iinB'] if rrd['iinB'] else rrd['betB']
        out_beg = rrd['outB'] if rrd['outB'] else rrd['winB']
        bet_beg = rrd['betB']
        win_beg = rrd['winB']
        self.maintshot_id = self.maintshot_id.create({
            'slot_id': self.id,
            'date_beg': get_now(),
            'iin_beg': iin_beg,
            'out_beg': out_beg,
            'bet_beg': bet_beg,
            'win_beg': win_beg,
        })
        return

    @api.multi
    def repair_end(self):
        date_beg = self.maintshot_id.date_beg
        date_end = get_now()
        rrd = get_data_rrd(self.dev_sn, date_beg, date_end)
        iin_beg = rrd['iinB'] if rrd['iinB'] else rrd['betB']
        iin_end = rrd['iinE'] if rrd['iinE'] else rrd['betE']
        out_beg = rrd['outB'] if rrd['outB'] else rrd['winB']
        out_end = rrd['outE'] if rrd['outE'] else rrd['winE']
        bet_beg = rrd['betB']
        bet_end = rrd['betE']
        win_beg = rrd['winB']
        win_end = rrd['winE']
        self.maintshot_id.write({
            'slot_id': self.id,
            'index':   self.index,
            'date_beg': date_beg,
            'date_end': date_end,
            'iin_beg': iin_beg,
            'iin_end': iin_end,
            'out_beg': out_beg,
            'out_end': out_end,
            # 'iin': iin_end - iin_beg,
            # 'out': out_end - out_beg,
            'bet_beg': bet_beg,
            'bet_end': bet_end,
            'win_beg': win_beg,
            'win_end': win_end,
            # 'bet': bet_end - bet_beg,
            # 'win': win_end - win_beg,
        })
        self.maintshot_id = None
        return

    # @api.depends('dev_sn')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = rec.dev_sn if rec.dev_sn else "Unknown"

