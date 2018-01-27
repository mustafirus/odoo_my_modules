# -*- coding: utf-8 -*-
from time import gmtime,localtime, mktime
import datetime
from odoo import models, fields, api
import json
import urllib2
import werkzeug.urls

GAMBLING_ENDPOINT = 'http://localhost:4000/counters'
GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000'


def get_now():
    return fields.datetime.now().replace(second=0, microsecond=0).strftime(fields.DATETIME_FORMAT)


def get_data_rrd(devid, date_beg, date_end):
    url = GAMBLING_ENDPOINT + '/counters?'
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    date_b = fields.Datetime.from_string(date_beg)
    date_e = fields.Datetime.from_string(date_end)
    date_b = int(mktime(date_b.timetuple()))
    date_e = int(mktime(date_e.timetuple()))

    reqargs = werkzeug.url_encode({
        'dateB': date_b,
        'dateE': date_e,
        'devid': devid,
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
    return content


class Hall(models.Model):
    _name = 'slot_machine_counters.hall'

    name = fields.Char('Name of hall')
    description = fields.Text('Description')
    hub_sn = fields.Char("Hub SN")
    hub_sim = fields.Char("Hub SIM")
    phone = fields.Char("Phone of admin")
    AlarmSms = fields.Boolean("Sms Alarm")
    AlarmPhone1 = fields.Char("Alarm Phone 1")
    AlarmPhone2 = fields.Char("Alarm Phone 2")
    gpslat = fields.Float("Geo Lat")
    gpslng = fields.Float("Geo Long")
    slot_ids = fields.One2many("slot_machine_counters.slot","hall_id","Slots")
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
        if 'slot_ids' in vals:
            for i in range(0,len(vals['slot_ids'])):
                if vals['slot_ids'][i][0] == 2:
                    vals['slot_ids'][i][0] = 3
        ret = super(Hall, self).write(vals)
        self._set_config()
        return ret



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
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    maintshot_id = fields.Many2one('slot_machine_counters.maintshot.line', string='Maintenance Slotshot')
    active = fields.Boolean('Active?', default=True)

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
    def repair_begin(self):
#        slotline = self.env['slot_machine_counters.maintshot.line']
#        rrd = get_data_rrd(self.dev_sn)
        self.maintshot_id = self.maintshot_id.create({
            'slot_id': self.id,
            'date_beg': get_now(),
        })
        return

    @api.multi
    def repair_end(self):
        date_beg = self.maintshot_id.date_beg
        date_end = get_now()
        rrd = get_data_rrd(self.dev_sn, date_beg, date_end)
        self.maintshot_id.write({
            'slot_id': self.id,
            'index':   self.index,
            'date_beg': date_beg,
            'date_end': date_end,
            'iin_beg': rrd['iinB'] if rrd['iinB'] else rrd['betB'],
            'iin_end':   rrd['iinE'] if rrd['iinE'] else rrd['betE'],
            'out_beg': rrd['outB'] if rrd['outB'] else rrd['winB'],
            'out_end':   rrd['outE'] if rrd['outE'] else rrd['winE'],
            'bet_beg': rrd['betB'],
            'bet_end': rrd['betE'],
            'win_beg': rrd['winB'],
            'win_end': rrd['winE'],
        })
        self.maintshot_id = None
        return

    # @api.depends('dev_sn')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = rec.dev_sn if rec.dev_sn else "Unknown"


class SlotShot(models.Model):
    _name = 'slot_machine_counters.slotshot'
    _description = 'SlotShot'

    @api.model
    def _get_now(self):
        return get_now()

    name = fields.Char("Name", readonly=True)
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall", required=True)
    date_beg = fields.Datetime("From", required=True, default=_get_now)
    date_end = fields.Datetime("To", required=True, default=_get_now)
    slotshot_lines = fields.One2many('slot_machine_counters.slotshot.line', 'slotshot_id', string='Slotshot Lines')
    credit     = fields.Integer("Credit",compute='_compute_total', readonly=True, store=True)
    amount     = fields.Monetary("Cash",compute='_compute_total', readonly=True, store=True)
    credit_bw     = fields.Integer("Credit BetWin",compute='_compute_total', readonly=True, store=True)
    amount_bw     = fields.Monetary("Cash BetWin",compute='_compute_total', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('slot_machine_counters.slotshot')
        return super(SlotShot, self.with_context(self.env.context)).create(vals)


    @api.onchange('hall_id')  # if these fields are changed, call method
    def _set_date_beg(self):
        try:
            if not self.hall_id:
                return
            prevshot = self.env['slot_machine_counters.slotshot'].sudo(). \
                search([('hall_id.id', '=', self.hall_id.id), ('date_end', '!=', False)], limit=1, order='date_end desc')
            prevshot.ensure_one()
            self.date_beg = prevshot.date_end
        except:
            pass


    @api.depends('slotshot_lines.credit')
    def _compute_total(self):
        for rec in self:
            rec.credit = 0
            rec.amount = 0.0
            rec.credit_bw = 0
            rec.amount_bw = 0.0
            for line in rec.slotshot_lines:
                rec.credit += line.credit
                rec.amount += line.amount
                rec.credit_bw += line.credit_bw
                rec.amount_bw += line.amount_bw

    # @api.depends('hall_id', 'date_end')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = "%s/%s" % (rec.hall_id.name, rec.date_end) if rec.date_end and rec.hall_id else "---"

    @api.multi
    def print_data (self):
        self.ensure_one()
        rep = self.env['slot_machine_counters.hallreport']
        rep = rep.create({
            'hall_id':  self.hall_id.id,
            'date_beg': self.date_beg,
            'date_end': self.date_end,
            'full':     True,
        })
        return rep.print_rep(self)


    @api.multi
    def get_data(self):
        self.ensure_one()
        if not self.hall_id:
            return

        if self.date_end <= self.date_beg:
            self.date_end = self.date_beg

        ids = self.hall_id.slot_ids
        slotline = self.env['slot_machine_counters.slotshot.line']
        existing = slotline.browse(self.slotshot_lines._ids)
        existing.unlink()
        for slot in ids:
            rrd = get_data_rrd(slot.dev_sn, self.date_beg, self.date_end)
            vals = {
                'slotshot_id': self.id,
                'slot_id': slot.id,
                'index': slot.index,
                'iin_beg': rrd['iinB'] if rrd['iinB'] else rrd['betB'],
                'iin_end':   rrd['iinE'] if rrd['iinE'] else rrd['betE'],
                'out_beg': rrd['outB'] if rrd['outB'] else rrd['winB'],
                'out_end':   rrd['outE'] if rrd['outE'] else rrd['winE'],
                'bet_beg': rrd['betB'],
                'bet_end': rrd['betE'],
                'win_beg': rrd['winB'],
                'win_end': rrd['winE'],
            }
            slotline.create(vals)


class SlotShotLine(models.Model):
    _name = 'slot_machine_counters.slotshot.line'
    _description = 'SlotShot Line'
    _order = 'slotshot_id,index'

    slotshot_id = fields.Many2one('slot_machine_counters.slotshot', string='SlotShot Reference', required=False, ondelete='cascade', index=True, copy=False)
    index     = fields.Integer("Index")
    slot_id   = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_beg   = fields.Integer("in")
    iin_end   = fields.Integer("IN")
    out_beg   = fields.Integer("out")
    out_end   = fields.Integer("OUT")
    iin       = fields.Integer("IN-in",compute='_compute_iin', readonly=True, store=True)
    out       = fields.Integer("OUT-out",compute='_compute_out', readonly=True, store=True)
    credit    = fields.Integer("Credit",compute='_compute_credit', readonly=True, store=True)
    amount    = fields.Monetary("Cash",compute='_compute_amount', readonly=True, store=True)
    bet_beg   = fields.Integer("bet")
    bet_end   = fields.Integer("BET")
    win_beg   = fields.Integer("win")
    win_end   = fields.Integer("WIN")
    bet       = fields.Integer("BET-bet",compute='_compute_bet', readonly=True, store=True)
    win       = fields.Integer("WIN-win",compute='_compute_win', readonly=True, store=True)
    credit_bw = fields.Integer("Credit",compute='_compute_credit_bw', readonly=True, store=True)
    amount_bw = fields.Monetary("Cash",compute='_compute_amount_bw', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='slot_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
#################

    @api.depends('iin_beg','iin_end')
    def _compute_iin(self):
        for rec in self:
            rec.iin = (rec.iin_end - rec.iin_beg)

    @api.depends('out_beg','out_end')
    def _compute_out(self):
        for rec in self:
            rec.out = (rec.out_end - rec.out_beg)

    @api.depends('iin','out')
    def _compute_credit(self):
        for rec in self:
            rec.credit = rec.iin - rec.out

    @api.depends('credit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.credit * rec.slot_id.denomenation
#################

    @api.depends('bet_beg','bet_end')
    def _compute_bet(self):
        for rec in self:
            rec.bet = (rec.bet_end - rec.bet_beg)

    @api.depends('win_beg','win_end')
    def _compute_win(self):
        for rec in self:
            rec.win = (rec.win_end - rec.win_beg)

    @api.depends('bet','win')
    def _compute_credit_bw(self):
        for rec in self:
            rec.credit_bw = rec.bet - rec.win

    @api.depends('credit_bw')
    def _compute_amount_bw(self):
        for rec in self:
            rec.amount_bw = rec.credit_bw * rec.slot_id.denomenation
#################


class MaintShotLine(models.Model):
    _name = 'slot_machine_counters.maintshot.line'
    _description = 'MaintShot Line'

    @api.model
    def _get_now(self):
        return get_now()


    date_beg = fields.Datetime("From", required=True, default=_get_now)
    date_end = fields.Datetime("To", required=True, default=_get_now)

    slot_id   = fields.Many2one("slot_machine_counters.slot","Slot")
    index     = fields.Integer("Index")
    iin_beg   = fields.Integer("in")
    iin_end   = fields.Integer("IN")
    out_beg   = fields.Integer("out")
    out_end   = fields.Integer("OUT")
    iin       = fields.Integer("IN-in",compute='_compute_iin', readonly=True, store=True)
    out       = fields.Integer("OUT-out",compute='_compute_out', readonly=True, store=True)
    credit    = fields.Integer("Credit",compute='_compute_credit', readonly=True, store=True)
    amount    = fields.Monetary("Cash",compute='_compute_amount', readonly=True, store=True)
    bet_beg   = fields.Integer("bet")
    bet_end   = fields.Integer("BET")
    win_beg   = fields.Integer("win")
    win_end   = fields.Integer("WIN")
    bet       = fields.Integer("BET-bet",compute='_compute_bet', readonly=True, store=True)
    win       = fields.Integer("WIN-win",compute='_compute_win', readonly=True, store=True)
    credit_bw = fields.Integer("Credit",compute='_compute_credit_bw', readonly=True, store=True)
    amount_bw = fields.Monetary("Cash",compute='_compute_amount_bw', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='slot_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
#################
    @api.depends('iin_beg','iin_end')
    def _compute_iin(self):
        for rec in self:
            rec.iin = (rec.iin_end - rec.iin_beg)

    @api.depends('out_beg','out_end')
    def _compute_out(self):
        for rec in self:
            rec.out = (rec.out_end - rec.out_beg)

    @api.depends('iin','out')
    def _compute_credit(self):
        for rec in self:
            rec.credit = rec.iin - rec.out

    @api.depends('credit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.credit * rec.slot_id.denomenation
#################

    @api.depends('bet_beg','bet_end')
    def _compute_bet(self):
        for rec in self:
            rec.bet = (rec.bet_end - rec.bet_beg)

    @api.depends('win_beg','win_end')
    def _compute_win(self):
        for rec in self:
            rec.win = (rec.win_end - rec.win_beg)

    @api.depends('bet','win')
    def _compute_credit_bw(self):
        for rec in self:
            rec.credit_bw = rec.bet - rec.win

    @api.depends('credit_bw')
    def _compute_amount_bw(self):
        for rec in self:
            rec.amount_bw = rec.credit_bw * rec.slot_id.denomenation
#################


class HallReport(models.TransientModel):
    _name = 'slot_machine_counters.hallreport'
    _description = 'HallReport'

    hall_id = fields.Many2one("slot_machine_counters.hall","Hall", required=True)
    date_beg = fields.Datetime("From", required=True)
    date_end = fields.Datetime("To", required=True)
    full = fields.Boolean("Full report", default=False)
    hallreport_lines = fields.One2many('slot_machine_counters.hallreport.line', 'hallreport_id', string='Slotshot Lines')
    hallreport_maint = fields.One2many('slot_machine_counters.hallreport.maint', 'hallreport_id', string='Slotshot Lines')
    # credit     = fields.Integer("Credit",compute='_compute_total', readonly=True, store=True)
    amount     = fields.Monetary("Cash",compute='_compute_total', readonly=True, store=True)
    # credit_bw  = fields.Integer("Credit",compute='_compute_total', readonly=True, store=True)
    amount_bw  = fields.Monetary("Cash",compute='_compute_total', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    gps = fields.Char(compute="_set_data", readonly=True, store=True)

    @api.depends('hall_id')  # if these fields are changed, call method
    def _set_data(self):
        self.ensure_one()
        if not self.hall_id:
            return
        self.gps = "%s,%s" % (self.hall_id.gpslat,self.hall_id.gpslng)

    @api.depends('hallreport_lines.credit', 'hallreport_lines.credit_bw')
    def _compute_total(self):
        for rec in self:
            # rec.credit = 0
            rec.amount = 0.0
            # rec.credit_bw = 0
            rec.amount_bw = 0.0
            for line in rec.hallreport_lines:
                # rec.credit += line.credit
                rec.amount += line.amount
                # rec.credit_bw += line.credit_bw
                rec.amount_bw += line.amount_bw


    # def hallreport_print(self):
    #     return self._hallreport_print()


    @api.multi
    def hallreport_print(self):
        self.ensure_one()
        date_beg = fields.Date.from_string(self.date_beg)
        date_end = fields.Date.from_string(self.date_end)
        if date_end <= date_beg:
            date_end = date_beg + datetime.timedelta(days=1)
        date_beg = fields.Date.to_string(date_beg)
        date_end = fields.Date.to_string(date_end + datetime.timedelta(days=1))
        shots = self.env['slot_machine_counters.slotshot'].search([
            ('hall_id.id', '=', self.hall_id.id),
            ('date_beg', '>=', date_beg),
            ('date_end', '<', date_end),
        ])
        if not len(shots):
            return
        ft = shots[0]
        lt = shots[-1]
        self.date_beg = ft.date_beg
        self.date_end = lt.date_end
        return self.print_rep(shots)

    @api.multi
    def print_rep(self, shots):
        line_model=self.env['slot_machine_counters.hallreport.line']
        line_model.search([('hallreport_id', '=',  self.id)]).unlink()
        maint_model=self.env['slot_machine_counters.hallreport.maint']
        maint_model.search([('hallreport_id', '=',  self.id)]).unlink()
        self.env.cr.execute("""
            SELECT slot_id, string_agg(distinct cast(index as text), ','),
            min(iin_beg) as iin_beg, max(iin_end) as iin_end, sum(iin) as iin,
            min(out_beg) as out_beg, max(out_end) as out_end, sum(out) as out,
            sum(credit) as credit, sum(amount) as amount,
            min(bet_beg) as bet_beg, max(bet_end) as bet_end, sum(bet) as bet,
            min(win_beg) as win_beg, max(win_end) as win_end, sum(win) as win,
            sum(credit_bw) as credit_bw, sum(amount_bw) as amount_bw
            FROM slot_machine_counters_slotshot_line where slotshot_id in %s group by slot_id ;
        """, (tuple(shots.ids),))
        line_res = self.env.cr.fetchall()
        print line_res
        slots = zip(*line_res)[0]

        self.env.cr.execute("""
            SELECT slot_id, string_agg(distinct cast(index as text), ','),
            min(iin_beg) as iin_beg, max(iin_end) as iin_end, sum(iin) as iin,
            min(out_beg) as out_beg, max(out_end) as out_end, sum(out) as out,
            sum(credit) as credit, sum(amount) as amount,
            min(bet_beg) as bet_beg, max(bet_end) as bet_end, sum(bet) as bet,
            min(win_beg) as win_beg, max(win_end) as win_end, sum(win) as win,
            sum(credit_bw) as credit_bw, sum(amount_bw) as amount_bw
            FROM slot_machine_counters_maintshot_line where slot_id in %s and date_beg >= %s and date_end < %s
            group by slot_id ;
        """, (tuple(slots), self.date_beg, self.date_end, ))
        maint_res = self.env.cr.fetchall()
        print maint_res
        maint_dict = dict(map(lambda x: (x[0],x),maint_res))

        for line in line_res:
            maint = maint_dict.get(line[0], (line[0], u'', 0, 0, 0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0))
            vals = {
                'hallreport_id':  self.id,
                'slot_id':    line[0],
                'index': line[1],
                'iin_beg': line[2],
                'iin_end': line[3],
                'iin': line[4] - maint[4],
                'out_beg': line[5],
                'out_end': line[6],
                'out': line[7] - maint[7],
                'credit': line[8] - maint[8],
                'amount': line[9] - maint[9],
                'bet_beg': line[10],
                'bet_end': line[11],
                'bet': line[12] - maint[12],
                'win_beg': line[13],
                'win_end': line[14],
                'win': line[15] - maint[15],
                'credit_bw': line[16] - maint[16],
                'amount_bw': line[17] - maint[17],
            }
            line_model.create(vals)

        for maint in maint_res:
            vals = {
                'hallreport_id':  self.id,
                'slot_id':    maint[0],
                'index': maint[1],
                'iin_beg': maint[2],
                'iin_end': maint[3],
                'iin': maint[4] - maint[4],
                'out_beg': maint[5],
                'out_end': maint[6],
                'out': maint[7] - maint[7],
                'credit': maint[8] - maint[8],
                'amount': maint[9] - maint[9],
                'bet_beg': maint[10],
                'bet_end': maint[11],
                'bet': maint[12] - maint[12],
                'win_beg': maint[13],
                'win_end': maint[14],
                'win': maint[15] - maint[15],
                'credit_bw': maint[16] - maint[16],
                'amount_bw': maint[17] - maint[17],
            }
            maint_model.create(vals)

        return self.env['report'].get_action(self, 'slot_machine_counters.hallreport_multi')

class HallReportLine(models.TransientModel):
    _name = 'slot_machine_counters.hallreport.line'
    _description = 'HallReport Line'
    _order = 'hallreport_id,index'

    hallreport_id = fields.Many2one('slot_machine_counters.hallreport', string='HallReport Reference', required=True, ondelete='cascade', index=True, copy=False)
    index     = fields.Char("Index")
    slot_id   = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_beg   = fields.Integer()
    iin_end   = fields.Integer()
    out_beg   = fields.Integer()
    out_end   = fields.Integer()
    iin       = fields.Integer(readonly=True, store=True)
    out       = fields.Integer(readonly=True, store=True)
    credit = fields.Integer(readonly=True, store=True)
    amount = fields.Monetary(readonly=True, store=True)
    bet_beg   = fields.Integer()
    bet_end   = fields.Integer()
    win_beg   = fields.Integer()
    win_end   = fields.Integer()
    bet       = fields.Integer(readonly=True, store=True)
    win       = fields.Integer(readonly=True, store=True)
    credit_bw = fields.Integer(readonly=True, store=True)
    amount_bw = fields.Monetary(readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hallreport_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')

class HallReportMaint(models.TransientModel):
    _name = 'slot_machine_counters.hallreport.maint'
    _description = 'HallReport Maint'
    _order = 'hallreport_id,index'

    hallreport_id = fields.Many2one('slot_machine_counters.hallreport', string='HallReport Reference', required=True, ondelete='cascade', index=True, copy=False)
    index     = fields.Char("Index")
    slot_id   = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_beg   = fields.Integer()
    iin_end   = fields.Integer()
    out_beg   = fields.Integer()
    out_end   = fields.Integer()
    iin       = fields.Integer(readonly=True, store=True)
    out       = fields.Integer(readonly=True, store=True)
    credit = fields.Integer(readonly=True, store=True)
    amount = fields.Monetary(readonly=True, store=True)
    bet_beg   = fields.Integer()
    bet_end   = fields.Integer()
    win_beg   = fields.Integer()
    win_end   = fields.Integer()
    bet       = fields.Integer(readonly=True, store=True)
    win       = fields.Integer(readonly=True, store=True)
    credit_bw = fields.Integer(readonly=True, store=True)
    amount_bw = fields.Monetary(readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hallreport_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
