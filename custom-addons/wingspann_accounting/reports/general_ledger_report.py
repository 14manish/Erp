# -*- coding: utf-8 -*-
from odoo import models, api

class ReportGeneralLedger(models.AbstractModel):
    _name = 'report.wingspann_accounting.report_general_ledger'
    _description = 'General Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        target_move = data['form']['target_move']
        account_ids = data['form'].get('account_ids', [])

        domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        if target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        if account_ids:
            domain.append(('account_id', 'in', account_ids))

        move_lines = self.env['account.move.line'].search(domain, order='date, id')

        accounts = {}
        for line in move_lines:
            acc = line.account_id
            if acc not in accounts:
                accounts[acc] = {'lines': [], 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
            accounts[acc]['lines'].append(line)
            accounts[acc]['debit'] += line.debit
            accounts[acc]['credit'] += line.credit
            accounts[acc]['balance'] += (line.debit - line.credit)

        # Calculate opening balances (before date_from)
        for acc in accounts:
            open_domain = [('date', '<', date_from), ('account_id', '=', acc.id)]
            if target_move == 'posted':
                open_domain.append(('parent_state', '=', 'posted'))
            open_lines = self.env['account.move.line'].search(open_domain)
            initial_balance = sum(l.debit - l.credit for l in open_lines)
            accounts[acc]['initial_balance'] = initial_balance
            accounts[acc]['balance'] += initial_balance

        return {
            'doc_ids': docids,
            'doc_model': 'wingspann.general.ledger.wizard',
            'data': data['form'],
            'accounts': accounts,
            'company': self.env.company,
        }
