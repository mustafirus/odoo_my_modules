# -*- coding: utf-8 -*-
from time import gmtime,localtime, mktime
import datetime


from odoo import models, fields, api
import json
import urllib2
import logging
import werkzeug.urls

from odoo.exceptions import UserError
from slot_machine_counters.rrd import get_data_rrd

GAMBLING_ENDPOINT = 'http://localhost:4000/counters'
GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000'

_logger = logging.getLogger(__name__)

def get_now():
    return fields.datetime.now().replace(second=0, microsecond=0).strftime(fields.DATETIME_FORMAT)

def get_midnight():
    return fields.datetime.now().replace(hour=0,minute=0,second=0, microsecond=0).strftime(fields.DATETIME_FORMAT)


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
    def shot(self, hall_id, type):
        if not hall_id:
            return
        if type == 'start':
            date_beg = get_now()
            date_end = get_now()
            pass
        elif type == 'stop':
            date_beg = self._get_date_beg(hall_id)
            date_end = get_now()
            pass
        elif type == 'daily':
            date_beg = self._get_date_beg(hall_id)
            date_end = get_midnight()
            pass
        elif type == 'now':
            date_beg = self._get_date_beg(hall_id)
            date_end = get_now()
            pass
        else:
            return

        if type != 'start' and date_beg == date_end:
            return

        vals = {
            'hall_id': hall_id.id,
            'date_beg': date_beg,
            'date_end': date_end,
        }
        shot = self.create(vals)
        shot.get_data()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('slot_machine_counters.slotshot')
        return super(SlotShot, self.with_context(self.env.context)).create(vals)

    def _get_date_beg(self, hall_id):
        try:
            prevshot = self.env['slot_machine_counters.slotshot'].sudo(). \
                search([('hall_id.id', '=', hall_id.id), ('date_end', '!=', False)], limit=1, order='date_end desc')
            prevshot.ensure_one()
            return prevshot.date_end
        except:
            pass

    @api.onchange('hall_id')  # if these fields are changed, call method
    def _set_date_beg(self):
        try:
            if not self.hall_id:
                return
            self.date_beg = self._get_date_beg(self.hall_id)
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
            if slot.maintshot_id:
                raise UserError("Maintance in progress! Try again later.")
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
            if rec.date_end is not None:
                rec.iin = (rec.iin_end - rec.iin_beg)

    @api.depends('out_beg','out_end')
    def _compute_out(self):
        for rec in self:
            if rec.date_end is not None:
                rec.out = (rec.out_end - rec.out_beg)

    @api.depends('iin','out')
    def _compute_credit(self):
        for rec in self:
            if rec.date_end is not None:
                rec.credit = rec.iin - rec.out

    @api.depends('credit')
    def _compute_amount(self):
        for rec in self:
            if rec.date_end is not None:
                rec.amount = rec.credit * rec.slot_id.denomenation
#################

    @api.depends('bet_beg','bet_end')
    def _compute_bet(self):
        for rec in self:
            if rec.date_end is not None:
                rec.bet = (rec.bet_end - rec.bet_beg)

    @api.depends('win_beg','win_end')
    def _compute_win(self):
        for rec in self:
            if rec.date_end is not None:
                rec.win = (rec.win_end - rec.win_beg)

    @api.depends('bet','win')
    def _compute_credit_bw(self):
        for rec in self:
            if rec.date_end is not None:
                rec.credit_bw = rec.bet - rec.win

    @api.depends('credit_bw')
    def _compute_amount_bw(self):
        for rec in self:
            if rec.date_end is not None:
                rec.amount_bw = rec.credit_bw * rec.slot_id.denomenation
#################


