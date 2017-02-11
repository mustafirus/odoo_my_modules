# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _

class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Tickets"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['helpdesk.stage'].search("", order='sequence', limit=1)

    name = fields.Char(string='Ticket', required=True)
    description = fields.Text('Private Note')
    partner_id = fields.Many2one('res.partner', string='Customer', index=True)
    contact_name = fields.Char('Contact Name')
    email_from = fields.Char('Email', help="Email address of the contact", index=True)
    user_id = fields.Many2one('res.users', string='Assigned to', index=True, track_visibility='onchange', default=False)
    team_id = fields.Many2one('helpdesk.team', string='Support Team',
        default=lambda self: self.env['helpdesk.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, track_visibility='onchange', help='When sending mails, the default email address is taken from the sales team.')
    date_deadline = fields.Datetime(string='Deadline')

    stage_id = fields.Many2one('helpdesk.stage', string='Stage', track_visibility='onchange', index=True,
                               domain="[]",
                               copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High'), ('3', 'Urgent')], 'Priority', index=True, default='1')
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')], string='Kanban State',
                                    track_visibility='onchange', required=True, default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this ticket\n
                                           * Ready for next stage indicates the ticket is ready to be closed""")

    color = fields.Integer('Color Index')
    legend_blocked = fields.Char(related="stage_id.legend_blocked", string='Kanban Blocked Explanation', readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", string='Kanban Valid Explanation', readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", string='Kanban Ongoing Explanation', readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(name=_('%s (copy)') % (self.name))
        return super(HelpdeskTicket, self).copy(default=default)

    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        # if vals.get('user_id') and not vals.get('date_open'):
        #     vals['date_open'] = fields.Datetime.now()
        # if 'stage_id' in vals:
        #     vals.update(vals['stage_id'])

        # context: no_log, because subtype already handle this
        context['mail_create_nolog'] = True
        return super(HelpdeskTicket, self.with_context(context)).create(vals)

    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            # vals.update(vals['stage_id'])
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        # user_id change: update date_open
        # if vals.get('user_id') and 'date_open' not in vals:
        #     vals['date_open'] = fields.Datetime.now()
        return super(HelpdeskTicket, self).write(vals)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def takeit(self):
        self.ensure_one()
        vals = {'user_id' : self.env.uid,
                'team_id': self.env['helpdesk.team'].sudo()._get_default_team_id(user_id=self.env.uid).id}
        return super(HelpdeskTicket, self).write(vals)
