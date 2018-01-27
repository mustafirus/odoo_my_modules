# -*- coding: utf-8 -*-

import base64
import json
import urllib
import urllib2
from urllib2 import HTTPError

import time

from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.base.res.res_bank import sanitize_account_number

CLIENTID = ""
CLIENTSECRET = ""


import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _name = 'privat24.import'
    _inherit = 'account.bank.statement.import'

    data_file = fields.Binary(required=False, store=False)
    filename = fields.Char(store=False)

    journal_id = fields.Many2one("account.journal")#, default=_default_journal)
    privat24_date = fields.Date(string="Date")
    privat24_login = fields.Char(related='journal_id.privat24_login',string="Username")
    privat24_pass = fields.Char(related='journal_id.privat24_pass',string="Password")
    privat24_savepass = fields.Boolean(related='journal_id.privat24_savepass',string="Save password")
    privat24_otp = fields.Char("OTP")
    privat24_lastsync = fields.Date(related='journal_id.privat24_lastsync',string="Start Date")

    # @api.multi
    # def write(self, values):
    #     return super(AccountBankStatementImport, self).write(values)
    #
    # @api.model
    # def create(self, values):
    #     return super(AccountBankStatementImport, self).create(values)
    #

    @api.multi
    def privat24_auth(self):
        now = time.time()
        # self.journal_id.privat24_session = False
        if not self.journal_id.privat24_session or self.journal_id.privat24_session_exp <= now:
            dd = self.request_privat24_url("/api/auth/createSession",
                                           post={"clientId":CLIENTID,"clientSecret":CLIENTSECRET},
                                           headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
                                       )
            if 'ROLE_CLIENT' not in dd['roles']:
                raise UserError(dd)
            self.journal_id.privat24_session = dd['id']
            self.journal_id.privat24_session_exp = dd['expiresIn']

        dd = self.request_privat24_url("/api/auth/validateSession",
                                       post={"sessionId": self.journal_id.privat24_session,},
                                       headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
                                       )

        if 'ROLE_P24_BUSINESS' not in dd['roles']:
            dd = self.request_privat24_url("/api/p24BusinessAuth/createSession",
                                           post={"sessionId": self.journal_id.privat24_session,
                                                 "login":self.privat24_login,
                                                 "password":self.privat24_pass},
                                           headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
                                           )

        # dd['message'] = [{"id": "1111111", "number": "050...111"},
        #                  {"id": "1111112", "number": "068...112"},
        #                  {"id": "1111112", "number": "095...113"}]
        # dd['message'] = "Confirm authorization with OTP"
        # dd['roles'].remove('ROLE_P24_BUSINESS')
        if 'ROLE_P24_BUSINESS' not in dd['roles']:
            if dd['message'] == "Confirm authorization with OTP":
                return {
                    'name': 'Import',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_model': self._name,  # 'privat24.import',
                    'res_id': self.id,  # 'privat24.import',
                    'type': 'ir.actions.act_window',
                    'view_id': self.env.ref('privat24_sync.account_bank_statement_import_view_otp').id,
                }
            elif isinstance(dd['message'], list):
                raise UserError("multiply phones not supported")
            else:
                raise UserError(str(dd))

        context = {key: self._context[key] for key in self._context if key not in ['default_journal_id', 'default_privat24_login', 'default_privat24_pass', 'default_privat24_savepass']}
        return self.with_context(context).import_privat24()



        # dd = self.request_privat24_url("/api/auth/createSession",
        #                                post={"clientId":"1ec12c0e-c304-4b6e-ba2c-50e2bdc295e3","clientSecret":"0524b287ae7a86b28794687e73811b97"},
        #                                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
        #                           )
        # session = dd[u'id']
        # expiresIn = dd[u'expiresIn']
        pass

    @api.multi
    def privat24_authotp(self):
        dd = self.request_privat24_url("/api/p24BusinessAuth/checkOtp",
                                       post={"sessionId": self.journal_id.privat24_session,
                                             "otp": self.privat24_otp},
                                       headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
                                       )
        if 'ROLE_P24_BUSINESS' not in dd['roles']:
                raise UserError(str(dd))
        context = {key: self._context[key] for key in self._context if key not in ['default_journal_id', 'default_privat24_login', 'default_privat24_pass', 'default_privat24_savepass']}
        return self.with_context(context).import_privat24()



    @api.model
    def request_privat24_url(self, url, post=None, headers=None, raiseit=True, **params):
        host = 'link.privatbank.ua'
        url = 'https://{}{}'.format(host, url)
        p = urllib.urlencode(params)
        if p:
            url += '?' + p
        body = post
        if body:
            body = json.dumps(body)

        request = urllib2.Request(
            url=url,
            data=body,
            headers=headers
        )

        try:
            response = urllib2.urlopen(request)
        except HTTPError as e:
            rr = e.fp.read()
            err = json.loads(rr.decode('utf8')).get('error')
            msg = '{} ({})'.format(e, err)
            _logger.exception(msg)
            raise UserError(msg)

        rr = response.read()
        response_data = json.loads(rr.decode('utf8'))
        # if response.code != 200:
        #     error = response_data.get('error')
        #     msg = '{}: {}({})'.format(response.status, response.reason, error)
        #     _logger.exception(msg)
        #     raise UserError(msg)
        # error = response_data.get('error')
        # if error:
        #     _logger.exception('request_privat24_url({}):{}, json: {}'.format(url, error, body))
        #     if raiseit:
        #         raise UserError(_(error))
        return response_data


    @api.multi
    def import_privat24(self):
        """ Process the file chosen in the wizard, create bank statement(s) and go to reconciliation. """
        self.ensure_one()
        startdate = fields.Date.from_string(self.privat24_lastsync).strftime("%d.%m.%Y")#"%Y-%m-%d"
        enddate = fields.date.today().strftime("%d.%m.%Y")
        dd = self.request_privat24_url("/api/p24b/statements",
                                       headers={'Authorization': 'Token '+self.journal_id.privat24_session,'Content-Type': 'application/json', 'Accept': 'application/json'},
                                       acc=self.journal_id.bank_acc_number, stdate=startdate, endate=enddate #,showInf=1
                                       )

        # Let the appropriate implementation module parse the file and return the required data
        # The active_id is passed in context in case an implementation module requires information about the wizard state (see QIF)
        currency_code, account_number, stmts_vals = self.with_context(active_id=self.ids[0])._parse_file(dd)
        # Check raw data
        self._check_parsed_data(stmts_vals)
        # Try to find the currency and journal in odoo
        currency, journal = self._find_additional_data(currency_code, account_number)
        # If no journal found, ask the user about creating one
        # if not journal:
        #     # The active_id is passed in context so the wizard can call import_file again once the journal is created
        #     return self.with_context(active_id=self.ids[0])._journal_creation_wizard(currency, account_number)
        if not journal.default_debit_account_id or not journal.default_credit_account_id:
            raise UserError(_('You have to set a Default Debit Account and a Default Credit Account for the journal: %s') % (journal.name,))
        # Prepare statement data to be used for bank statements creation
        stmts_vals = self._complete_stmts_vals(stmts_vals, journal, account_number)
        # Create the bank statements
        statement_ids, notifications = self._create_bank_statements(stmts_vals)
        # Now that the import worked out, set it as the bank_statements_source of the journal
        journal.bank_statements_source = 'privat24_import'
        # Finally dispatch to reconciliation interface
        action = self.env.ref('account.action_bank_reconcile_bank_statements')
        self.privat24_lastsync = fields.date.today()
        return {
            'name': action.name,
            'tag': action.tag,
            'context': {
                'statement_ids': statement_ids,
                'notifications': notifications
            },
            'type': 'ir.actions.client',
        }


    def _parse_file(self, data):
        """ Each module adding a file support must extends this method. It processes the file if it can, returns super otherwise, resulting in a chain of responsability.
            This method parses the given file and returns the data required by the bank statement import process, as specified below.
            rtype: triplet (if a value can't be retrieved, use None)
                - currency code: string (e.g: 'EUR')
                    The ISO 4217 currency code, case insensitive
                - account number: string (e.g: 'BE1234567890')
                    The number of the bank account which the statement belongs to
                - bank statements data: list of dict containing (optional items marked by o) :
                    - 'name': string (e.g: '000000123')
                    - 'date': date (e.g: 2013-06-26)
                    -o 'balance_start': float (e.g: 8368.56)
                    -o 'balance_end_real': float (e.g: 8888.88)
                    - 'transactions': list of dict containing :
                        - 'name': string (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
                        - 'date': date
                        - 'amount': float
                        - 'unique_import_id': string
                        -o 'account_number': string
                            Will be used to find/create the res.partner.bank in odoo
                        -o 'note': string
                        -o 'partner_name': string
                        -o 'ref': string
        """
        zzz=json.dumps(data,indent=4)
        stmt=dict()
        cur = self.journal_id.currency_id or self.journal_id.company_id.currency_id
        for row in data:
            if row['amount']['@ccy'] != cur.name:
                continue
            if row['info']['@flinfo'] != 'r':
                continue
            if row['info']['@state'] != 'r':
                continue

            dt = row['info']['@postdate'][0:8]
            dt = datetime.strptime(dt, "%Y%m%d").date() #u'20170901T09:46:00'
            dt = fields.Date.to_string(dt)
            accd = row['debet']['account']['@number']
            mfod = row['debet']['account']['customer']['bank']['@code']
            accc = row['credit']['account']['@number']
            mfoc = row['credit']['account']['customer']['bank']['@code']
            myacc = self.journal_id.bank_account_id.acc_number
            mymfo = self.journal_id.bank_account_id.bank_bic
            amt = float(row['amount']['@amt'])
            if accc == myacc and mfoc == mymfo:
                acc = accd
                pn = row['debet']['account']['@name']
            elif accd == myacc and mfod == mymfo:
#                amt = -amt
                acc = accc
                pn = row['credit']['account']['@name']
            else:
                raise UserError(_('Unknown account\n'))

            if not stmt.get(dt):
                stmt[dt] = {
                    'name': self.env['ir.sequence'].next_by_code('privat24_sync.statements'),
                    'date': dt,
                    # 'balance_start': None,
                    # 'balance_end_real': None,
                    'transactions': [],
                    }
            stmt[dt]['transactions'].append({
                'name': pn,
                'date': dt,
                'amount': amt,
                'unique_import_id': row['info']['@ref'],
                'account_number': acc,
                'note': row['purpose'],
                'partner_name': pn,
                'ref': '',
            })

        return (cur.name,self.journal_id.bank_acc_number, stmt.values())
        # raise UserError(_('Could not make sense of the given file.\nDid you install the module to support this type of file ?'))





