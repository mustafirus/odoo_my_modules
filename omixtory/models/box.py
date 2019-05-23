from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Box(models.Model):
    _name = "omixtory.box"
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'box already exists!'),
    ]

    name = fields.Char('FQDN', compute='_compute_name', store=True)
    dc = fields.Char('Boxname', required=True, default='pm1')
    domain = fields.Char('Domain', compute='_compute_domain', required=True)
    client_id = fields.Many2one(related='site_id.client_id')
    site_id = fields.Many2one('omixtory.site', domain="[('client_id', '=', client_id)]",
                              ondelete="cascade", required=True)
    ip = fields.Char('IP')
    direct_ip = fields.Char('Direct IP', required=True)
    direct_port = fields.Char('Direct port', default='22', required=True)

    ssh_url = fields.Char('ssh', compute='_compute_ssh_url')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('normal', 'Normal')
    ], default='draft')
    active = fields.Boolean(default=True)

    @api.depends('site_id.dc')
    def _compute_domain(self):
        for rec in self:
            rec.domain = rec.site_id.get_domain() if rec.site_id else ''

    @api.depends('dc', 'domain')
    def _compute_name(self):
        for rec in self:
            if rec.dc:
                rec.name = rec.dc + '.' + rec.domain
            pass

    @api.depends('name')
    def _compute_ssh_url(self):
        for rec in self:
            rec.ssh_url = 'ssh://root@' + rec.name if rec.name else ''


    @api.onchange('ip', 'site_id.arc')
    def _onchange_ip(self):
        if self.site_id.arc:
            self.direct_ip = self.ip

    @api.onchange('dc', 'site_id', 'site_id.box_network_prefix')
    def _onchange_site_id(self):
        if not self.site_id:
            return
        last_num = 255 - int(self.dc[2:])
        if last_num <= 250:
            last_num -= 1
        self.ip = self.site_id.box_network_prefix + '.' + str(last_num)

    @api.multi
    def write(self, vals):
        if 'active' in vals:
            vals['state'] = 'draft'
        return super(Box, self).write(vals)

    # @api.constrains('direct_ip')
    # def _validate_direct_ip(self):
    #     a = 1
    #     for rec in self:
    #         if rec.direct_ip == '0.0.0.0':
    #             raise ValidationError('Invalid IP!')
    #         elif rec.direct_ip == '127.0.0.127':
    #             rec.direct_ip = '0.0.0.0'
    #
    def _box_name(self, direct):
        return self.name.replace('.', 'd.', 1) if direct else self.name

    def _box_list(self, direct):
        res = []
        for rec in self:
            res.append(rec._box_name(direct))
        return res

    @api.multi
    def box_list(self):
        return self._box_list(False)

    @api.multi
    def box_list_d(self):
        return self._box_list(True)

    @api.multi
    def hostvars(self):
        vals = {}
        for r in self:
            if r.state != 'normal':
                continue
            vals.update({
                r._box_name(False): { 'ip': r.ip },
                r._box_name(True): { 'ansible_host': r.direct_ip, 'ansible_port': r.direct_port },
            })
        return vals
