# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class GeneralLedgerWizard(models.TransientModel):
    _name = 'wingspann.general.ledger.wizard'
    _description = 'General Ledger Report Wizard'

    def _default_date_from(self):
        # Default to start of current fiscal year (assuming Jan 1st for simplicity)
        return date(date.today().year, 1, 1)

    def _default_date_to(self):
        return date.today()

    date_from = fields.Date(string='Start Date', default=_default_date_from, required=True)
    date_to = fields.Date(string='End Date', default=_default_date_to, required=True)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', default='posted', required=True)
    
    account_ids = fields.Many2many('account.account', string='Accounts', help="Leave empty to print all accounts")

    def action_print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'target_move': self.target_move,
                'account_ids': self.account_ids.ids,
            }
        }
        return self.env.ref('wingspann_accounting.action_report_general_ledger').report_action(self, data=data)
