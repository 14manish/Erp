# -*- coding: utf-8 -*-
from odoo import models, api

class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.wingspann_accounting.report_partner_ledger'
    _description = 'Partner Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        target_move = data['form']['target_move']
        partner_type = data['form']['partner_type']
        partner_ids = data['form'].get('partner_ids', [])

        domain = [
            ('date', '>=', date_from), 
            ('date', '<=', date_to),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable'))
        ]
        
        if target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))
            
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        
        if partner_type == 'customer':
            domain.append(('account_id.account_type', '=', 'asset_receivable'))
        elif partner_type == 'supplier':
            domain.append(('account_id.account_type', '=', 'liability_payable'))

        move_lines = self.env['account.move.line'].search(domain, order='partner_id, date, id')

        partners = {}
        for line in move_lines:
            partner = line.partner_id
            if not partner:
                continue
            if partner not in partners:
                partners[partner] = {'lines': [], 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
            partners[partner]['lines'].append(line)
            partners[partner]['debit'] += line.debit
            partners[partner]['credit'] += line.credit
            partners[partner]['balance'] += (line.debit - line.credit)

        # Calculate opening balances
        for partner in partners:
            open_domain = [
                ('date', '<', date_from), 
                ('partner_id', '=', partner.id),
                ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable'))
            ]
            if target_move == 'posted':
                open_domain.append(('parent_state', '=', 'posted'))
            open_lines = self.env['account.move.line'].search(open_domain)
            initial_balance = sum(l.debit - l.credit for l in open_lines)
            partners[partner]['initial_balance'] = initial_balance
            partners[partner]['balance'] += initial_balance

        return {
            'doc_ids': docids,
            'doc_model': 'wingspann.partner.ledger.wizard',
            'data': data['form'],
            'partners': partners,
            'company': self.env.company,
        }
