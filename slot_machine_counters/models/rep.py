# -*- coding: utf-8 -*-
from time import gmtime,localtime, mktime
import datetime


from odoo import models, fields, api
import json
import urllib2
import logging
import werkzeug.urls

from odoo.exceptions import UserError

GAMBLING_ENDPOINT = 'http://localhost:4000/counters'
GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000'

_logger = logging.getLogger(__name__)



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
    amount_maint     = fields.Monetary("Cash",compute='_compute_total', readonly=True, store=True)
    amount_total     = fields.Monetary("Cash",compute='_compute_total', readonly=True, store=True)
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

    @api.depends('hallreport_lines.credit', 'hallreport_lines.credit_bw', 'hallreport_maint.credit')
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
            rec.amount_maint = 0.0
            for maint in rec.hallreport_maint:
                rec.amount_maint += maint.amount

            rec.amount_total = rec.amount - rec.amount_maint


    # def hallreport_print(self):
    #     return self._hallreport_print()


    @api.multi
    def hallreport_print(self):
        self.ensure_one()
        # date_beg = fields.Date.from_string(self.date_beg)
        # date_end = fields.Date.from_string(self.date_end)
        # if date_end <= date_beg:
        #     date_end = date_beg + datetime.timedelta(days=1)
        # date_beg = fields.Date.to_string(date_beg)
        # date_end = fields.Date.to_string(date_end + datetime.timedelta(days=1))
        date_beg = self.date_beg
        date_end = self.date_end
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
            FROM slot_machine_counters_slotshot_line where slotshot_id in %s group by slot_id order by min(index);
        """, (tuple(shots.ids),))
        line_res = self.env.cr.fetchall()
        _logger.debug("line_res")
        _logger.debug(line_res)
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
            group by slot_id order by min(index);
        """, (tuple(slots), self.date_beg, self.date_end, ))
        maint_res = self.env.cr.fetchall()
        _logger.debug("maint_res")
        _logger.debug(maint_res)
        maint_dict = dict(map(lambda x: (x[0],x),maint_res))

        for line in line_res:
            # maint = maint_dict.get(line[0], (line[0], u'', 0, 0, 0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0))
            vals = {
                'hallreport_id':  self.id,
                'slot_id':    line[0],
                'index': line[1],
                'iin_beg': line[2],
                'iin_end': line[3],
                'iin': line[4],
                'out_beg': line[5],
                'out_end': line[6],
                'out': line[7],
                'credit': line[8],
                'amount': line[9],
                'bet_beg': line[10],
                'bet_end': line[11],
                'bet': line[12],
                'win_beg': line[13],
                'win_end': line[14],
                'win': line[15],
                'credit_bw': line[16],
                'amount_bw': line[17],
            }
            line_model.create(vals)

        for maint in maint_res:
            vals = {
                'hallreport_id':  self.id,
                'slot_id':    maint[0],
                'index':        maint[1],
                'iin_beg':    maint[2],
                'iin_end':    maint[3],
                'iin':        maint[4],
                'out_beg':    maint[5],
                'out_end':    maint[6],
                'out':        maint[7],
                'credit':     maint[8],
                'amount':     maint[9],
                'bet_beg':    maint[10],
                'bet_end':    maint[11],
                'bet':        maint[12],
                'win_beg':    maint[13],
                'win_end':    maint[14],
                'win':        maint[15],
                'credit_bw':  maint[16],
                'amount_bw':  maint[17],
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
    iin       = fields.Integer()
    out       = fields.Integer()
    credit = fields.Integer()
    amount = fields.Monetary()
    bet_beg   = fields.Integer()
    bet_end   = fields.Integer()
    win_beg   = fields.Integer()
    win_end   = fields.Integer()
    bet       = fields.Integer()
    win       = fields.Integer()
    credit_bw = fields.Integer()
    amount_bw = fields.Monetary()
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
    iin       = fields.Integer()
    out       = fields.Integer()
    credit = fields.Integer()
    amount = fields.Monetary()
    bet_beg   = fields.Integer()
    bet_end   = fields.Integer()
    win_beg   = fields.Integer()
    win_end   = fields.Integer()
    bet       = fields.Integer()
    win       = fields.Integer()
    credit_bw = fields.Integer()
    amount_bw = fields.Monetary()
    currency_id = fields.Many2one('res.currency', related='hallreport_id.hall_id.company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
