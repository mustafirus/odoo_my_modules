from odoo import models, fields, api
from slot_machine_counters.rrd import get_data_rrd


def get_now():
    return fields.datetime.now().replace(microsecond=0).strftime(fields.DATETIME_FORMAT)


class Jackconf(models.Model):
    _name = 'slot_machine_counters.jackconf'
    _description = 'Jackpot config'

    name = fields.Char("Name", required=True)
    sequence = fields.Integer()
    # Config
    scope = fields.Selection([
            ('hall', 'One Hall'),
            ('all', 'All Halls'),
        ], required=True)
    start = fields.Integer("Start", required=True)
    max = fields.Integer("Max", required=True)
    coeficient = fields.Float('Coeficient', digits=(2,5), required=True)
    count = fields.Integer('Count', required=True)

    @api.model
    def create(self, vals):
        ret = super(Jackconf, self).create(vals)
        self.update_jackpots()
        return ret


    @api.model
    def update_jackpots(self):
        jpm = self.env['slot_machine_counters.jackpot']
        hallm = self.env['slot_machine_counters.hall']
        for conf in self.search([]):
            if conf.scope == 'all':
                if not jpm.search_count([('conf_id','=',conf.id),('hall_id','=',False)]):
                    jpm.create({
                        'conf_id': conf.id,
                    }).reset()
            if conf.scope == 'hall':
                for hall_id in hallm.search([]):
                    if hall_id.jackpot:
                        if not jpm.search_count([('conf_id', '=', conf.id), ('hall_id', '=', hall_id.id)]):
                            jpm.create({
                                'conf_id': conf.id,
                                'hall_id': hall_id.id,
                            }).reset()
                    else:
                        jpm.search([('hall_id', '=', hall_id.id)]).unlink()


class Jackpot(models.Model):
    _name = 'slot_machine_counters.jackpot'

    hall_id = fields.Many2one('slot_machine_counters.hall', "Hall")
    conf_id = fields.Many2one('slot_machine_counters.jackconf', "Conf")
    date = fields.Datetime()
    jack = fields.Integer("Jackpot")
    pot = fields.Integer("Games")
    state = fields.Selection([
        ('paused', 'Paused'),
        ('running', 'Running'),
        ('win', 'win'),
        ], string='Status', index=True, readonly=True, default='paused')

    def _update(self, date, jack, pot):
        if self.date >= date:
            return
        vals = {
            'date': date,
            'jack': jack,
            'pot' : pot,
        }
        self.write(vals)

    def _getjackpot_delta(self, hall_id, date):
        if self.date >= date:
            return 0, 0
        if self.state != 'running':
            return 0, 0
        if hall_id.state != 'running':
            return 0, 0
        jack = 0
        pot =  0
        for slot in hall_id.slot_ids:
            rrd = get_data_rrd(slot.dev_sn, self.date, date)
            if rrd['betB'] and rrd['betE']:
                jack += (rrd['betB'] - rrd['betE']) * self.conf_id.coeficient * slot.denomenation
                pot += rrd['winB'] - rrd['winE']
        return jack, pot

    def _getjackpot(self, date):
        if self.hall_id:
            jack, pot = self._getjackpot_delta(self.hall_id, date)
        else:
            jack, pot = 0, 0
            for hall_id in self.env['slot_machine_counters.hall'].search([('jackpot','=',True)]):
                j, p = self._getjackpot_delta(hall_id, date)
                jack += j
                pot += p
        return self.jack + jack, self.pot + pot if self.pot else self.pot

    @api.multi
    def getjack(self):
        date = get_now()
        self.ensure_one()
        jack, pot = self._getjackpot(date)
        if jack > self.conf_id.max and not self.pot:
            self._update(date, jack, 1)
        return jack

    @api.multi
    def update(self, date):
        for jp in self:
            jack, pot = jp._getjackpot(date)
            jp._update(date, jack, pot)

    @api.multi
    def pause(self):
        self.update(get_now())
        self.write({
            'state': 'running',
            'date': get_now(),
        })

    @api.multi
    def start(self):
        self.write({
            'state': 'running',
            'date': get_now(),
        })

    @api.multi
    def reset(self):
        for jp in self:
            jp.write({
                'state': 'running',
                'date': get_now(),
                'jack': jp.conf_id.start,
                'pot': 0,
            })

    @api.model
    def by_hall(self, hall_id):
        return self.search(['|',('hall_id','=',hall_id.id),('hall_id','=',False)])

    @api.model
    def by_hub_sn(self, hub_sn):
        hall_id = self.env['slot_machine_counters.hall'].search([('hub_sn', '=', hub_sn)])
        return self.by_hall(hall_id)
