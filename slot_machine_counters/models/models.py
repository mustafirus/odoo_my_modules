# -*- coding: utf-8 -*-
from time import gmtime,localtime, mktime
import datetime
from odoo import models, fields, api
import json
import urllib2
import werkzeug.urls


class Hall(models.Model):
    _name = 'slot_machine_counters.hall'

    name = fields.Char('Name of hall')
    description = fields.Text('Description')
    hub_sn = fields.Char("Hub SN")
    hub_sim = fields.Char("Hub SIM")
    phone = fields.Char("Phone of admin")
    gpslat = fields.Float("Geo Lat")
    gpslng = fields.Float("Geo Long")
    slot_ids = fields.One2many("slot_machine_counters.slot","hall_id","Slots")
    active = fields.Boolean('Active?', default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


class Slot(models.Model):
    _name = 'slot_machine_counters.slot'
    _rec_name = 'dev_sn'

    # name = fields.Char("Name", compute='_compute_name', readonly=True, store=True)
    index = fields.Integer("Index")
    dev_sn = fields.Char("SN Mega")
    slot_sn = fields.Char("SN Slot")
    type = fields.Char("Game type")
    denomenation = fields.Monetary("Denomenation")
    currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall")
    active = fields.Boolean('Active?', default=True)

    # @api.depends('dev_sn')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = rec.dev_sn if rec.dev_sn else "Unknown"


class SlotShot(models.Model):
    _name = 'slot_machine_counters.slotshot'
    _description = 'SlotShot'

    @api.model
    def _get_now(self):
        return fields.datetime.now().replace(second=0, microsecond=0).strftime(fields.DATETIME_FORMAT)

    name = fields.Char("Name", readonly=True)
    hall_id = fields.Many2one("slot_machine_counters.hall","Hall", required=True)
    date_beg = fields.Datetime("From", required=True, default=_get_now)
    date_end = fields.Datetime("To", required=True, default=_get_now)
    slotshot_lines = fields.One2many('slot_machine_counters.slotshot.line', 'slotshot_id', string='Slotshot Lines')
    credit     = fields.Integer("Credit",compute='_compute_total', readonly=True, store=True)
    amount     = fields.Monetary("$",compute='_compute_total', readonly=True, store=True)
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
            for line in rec.slotshot_lines:
                rec.credit += line.credit
                rec.amount += line.amount



    # @api.depends('hall_id', 'date_end')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = "%s/%s" % (rec.hall_id.name, rec.date_end) if rec.date_end and rec.hall_id else "---"


    def _get_data_rrd(self, devid):
        GAMBLING_ENDPOINT = 'http://localhost:4000/counters'
        GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000/counters?'
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        date_b = fields.Datetime.from_string(self.date_beg)
        date_e = fields.Datetime.from_string(self.date_end)
        date_b = int(mktime(date_b.timetuple()))
        date_e = int(mktime(date_e.timetuple()))

        reqargs = werkzeug.url_encode({
            'dateB': date_b,
            'dateE': date_e,
            'devid': devid,
        })
        try:
            req = urllib2.Request(GAMBLING_ENDPOINT + reqargs, None, headers)
            content = urllib2.urlopen(req, timeout=200).read()
        except urllib2.HTTPError:
            raise
        content = json.loads(content)
        err = content.get('error')
        if err:
            e = urllib2.HTTPError(req.get_full_url(), 999, err, headers, None)
            raise e
        return content

    @api.multi
    def get_data(self):
        self.ensure_one()
        if not self.hall_id:
            return
        ids = self.hall_id.slot_ids
        slotline = self.env['slot_machine_counters.slotshot.line']
        existing = slotline.browse(self.slotshot_lines._ids)
        existing.unlink()
        for slot in ids:
            rrd = self._get_data_rrd(slot.dev_sn)
            vals = {
                'slotshot_id': self.id,
                'slot_id': slot.id,
                'index': slot.index,
                'iin_beg': rrd['iinB'] if rrd['iinB'] else rrd['betB'],
                'iin_end':   rrd['iinE'] if rrd['iinE'] else rrd['betE'],
                'out_beg': rrd['outB'] if rrd['outB'] else rrd['winB'],
                'out_end':   rrd['outE'] if rrd['outE'] else rrd['winE'],
                'bet_beg': rrd['betB'],
                'bet_end': rrd['outE'],
                'win_beg': rrd['winB'],
                'win_end': rrd['winE'],
            }
            slotline.create(vals)
        a=1

class SlotShotLine(models.Model):
    _name = 'slot_machine_counters.slotshot.line'
    _description = 'SlotShot Line'
    _order = 'slotshot_id,index'

    slotshot_id = fields.Many2one('slot_machine_counters.slotshot', string='SlotShot Reference', required=True, ondelete='cascade', index=True, copy=False)
    index     = fields.Integer("Index")
    slot_id   = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_beg   = fields.Integer("in")
    iin_end   = fields.Integer("IN")
    out_beg   = fields.Integer("out")
    out_end   = fields.Integer("OUT")
    iin       = fields.Integer("IN-in",compute='_compute_iin', readonly=True, store=True)
    out       = fields.Integer("OUT-out",compute='_compute_out', readonly=True, store=True)
    credit    = fields.Integer("Credit",compute='_compute_credit', readonly=True, store=True)
    amount    = fields.Monetary("$",compute='_compute_amount', readonly=True, store=True)
    bet_beg   = fields.Integer("bet")
    bet_end   = fields.Integer("BET")
    win_beg   = fields.Integer("win")
    win_end   = fields.Integer("WIN")
    bet       = fields.Integer("BET-bet",compute='_compute_bet', readonly=True, store=True)
    win       = fields.Integer("WIN-win",compute='_compute_win', readonly=True, store=True)
    credit_bw = fields.Integer("Credit",compute='_compute_credit_bw', readonly=True, store=True)
    amount_bw = fields.Monetary("$",compute='_compute_amount_bw', readonly=True, store=True)
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

    @api.depends('iin_beg','out_beg','iin_end','out_end')
    def _compute_credit(self):
        for rec in self:
            rec.credit = (rec.iin_end - rec.iin_beg) - (rec.out_end - rec.out_beg)

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

    @api.depends('bet_beg','win_beg','bet_end','win_end')
    def _compute_credit_bw(self):
        for rec in self:
            rec.credit = (rec.bet_end - rec.bet_beg) - (rec.win_end - rec.win_beg)

    @api.depends('credit_bw')
    def _compute_amount_bw(self):
        for rec in self:
            rec.amount_bw = rec.credit_bw * rec.slot_id.denomenation
#################


class HallReport(models.TransientModel):
    _name = 'slot_machine_counters.hallreport'
    _description = 'HallReport'

    hall_id = fields.Many2one("slot_machine_counters.hall","Hall", required=True)
    date_beg = fields.Date("From", required=True)
    date_end = fields.Date("To", required=True)
    hallreport_lines = fields.One2many('slot_machine_counters.hallreport.line', 'hallreport_id', string='Slotshot Lines')
    credit     = fields.Integer("Credit",compute='_compute_total', readonly=True, store=True)
    amount     = fields.Monetary("$",compute='_compute_total', readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    gps = fields.Char(compute="_set_data", readonly=True, store=True)

    @api.depends('hall_id')  # if these fields are changed, call method
    def _set_data(self):
        self.ensure_one()
        if not self.hall_id:
            return
        self.gps = "%s,%s" % (self.hall_id.gpslat,self.hall_id.gpslng)


    @api.multi
    def hallreport_print(self):
        self.ensure_one()
        date_beg = fields.Date.from_string(self.date_beg)
        date_end = fields.Date.from_string(self.date_end)
        if date_end <= date_beg:
            date_end = date_beg + datetime.timedelta(days=1)
        date_beg = fields.Datetime.to_string(date_beg)
        date_end = fields.Datetime.to_string(date_end + datetime.timedelta(days=1))
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
        res = self.env.cr.fetchall()
        print res
        line_model=self.env['slot_machine_counters.hallreport.line']
        line_model.search([('hallreport_id', '=',  self.id)]).unlink()

        for line in res:
            vals = {
                'hallreport_id':  self.id,
                'slot_id':    line[0],
                'index': line[1],
                'iin_beg': line[2],
                'iin_end': line[3],
                'out_beg': line[4],
                'out_end': line[5],
                'iin': line[6],
                'out': line[7],
                'credit ': line[8],
                'amount ': line[9],
                'bet_beg': line[10],
                'bet_end': line[11],
                'win_beg': line[12],
                'win_end': line[13],
                'win': line[14],
                'bet': line[15],
                'credit_bw': line[16],
                'amount_bw': line[17],
            }
            line_model.create(vals)

        return self.env['report'].get_action(self, 'slot_machine_counters.hallreport_multi')

class HallReportLine(models.TransientModel):
    _name = 'slot_machine_counters.hallreport.line'
    _description = 'HallReport Line'
    _order = 'hallreport_id,index'

    hallreport_id = fields.Many2one('slot_machine_counters.hallreport', string='HallReport Reference', required=True, ondelete='cascade', index=True, copy=False)
    index = fields.Char("Index")
    slot_id = fields.Many2one("slot_machine_counters.slot","Slot")
    iin_beg = fields.Integer("in")
    iin_end   = fields.Integer("IN")
    out_beg = fields.Integer("out")
    out_end   = fields.Integer("OUT")
    iin       = fields.Integer("IN-in", readonly=True, store=True)
    out       = fields.Integer("OUT-out", readonly=True, store=True)
    credit     = fields.Integer("Credit", readonly=True, store=True)
    amount     = fields.Monetary("$", readonly=True, store=True)
    bet_beg = fields.Integer("bet")
    bet_end   = fields.Integer("BET")
    win_beg = fields.Integer("win")
    win_end   = fields.Integer("WIN")
    win       = fields.Integer("WIN-win", readonly=True, store=True)
    bet       = fields.Integer("BET-bet", readonly=True, store=True)
    credit_bw = fields.Integer("Credit", readonly=True, store=True)
    amount_bw = fields.Monetary("$", readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', related='hallreport_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
