# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class PartnerLedgerWizard(models.TransientModel):
    _name = 'wingspann.partner.ledger.wizard'
    _description = 'Partner Ledger Report Wizard'

    def _default_date_from(self):
        return date(date.today().year, 1, 1)

    def _default_date_to(self):
        return date.today()

    date_from = fields.Date(string='Start Date', default=_default_date_from, required=True)
    date_to = fields.Date(string='End Date', default=_default_date_to, required=True)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', default='posted', required=True)
    
    partner_type = fields.Selection([
        ('customer', 'Customer Only'),
        ('supplier', 'Vendor Only'),
        ('all', 'All Partners')
    ], string='Partner Type', default='all', required=True)
    
    partner_ids = fields.Many2many('res.partner', string='Partners', help="Leave empty to print all partners")

    def action_print_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'target_move': self.target_move,
                'partner_type': self.partner_type,
                'partner_ids': self.partner_ids.ids,
            }
        }
        return self.env.ref('wingspann_accounting.action_report_partner_ledger').report_action(self, data=data)
