# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountDashboard(models.TransientModel):
    _name = 'wingspann.accounting.dashboard'
    _description = 'Financial Dashboard Analytics'

    @api.model
    def get_dashboard_data(self):
        company_id = self.env.company.id

        # Cash & Bank Balances
        bank_cash_accounts = self.env['account.account'].search([
            ('account_type', 'in', ('asset_cash',)),
            ('company_id', '=', company_id)
        ])
        
        cash_balance = 0.0
        if bank_cash_accounts:
            self.env.cr.execute("""
                SELECT SUM(balance) FROM account_move_line
                WHERE account_id IN %s AND parent_state = 'posted'
            """, (tuple(bank_cash_accounts.ids),))
            res = self.env.cr.fetchone()
            cash_balance = res[0] if res and res[0] else 0.0

        # Receivables (Unpaid Customer Invoices)
        self.env.cr.execute("""
            SELECT SUM(amount_residual) FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'posted' AND payment_state IN ('not_paid', 'partial')
            AND company_id = %s
        """, (company_id,))
        res = self.env.cr.fetchone()
        receivables = res[0] if res and res[0] else 0.0

        # Payables (Unpaid Vendor Bills)
        self.env.cr.execute("""
            SELECT SUM(amount_residual) FROM account_move
            WHERE move_type = 'in_invoice' AND state = 'posted' AND payment_state IN ('not_paid', 'partial')
            AND company_id = %s
        """, (company_id,))
        res = self.env.cr.fetchone()
        payables = res[0] if res and res[0] else 0.0

        # Recent Activity (Last 10 posted moves)
        recent_moves = self.env['account.move'].search_read(
            [('state', '=', 'posted'), ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount_total', 'move_type', 'state'],
            limit=10,
            order='date desc, id desc'
        )
        
        TYPE_MAPPING = {
            'entry': 'Journal Entry',
            'out_invoice': 'Customer Invoice',
            'out_refund': 'Customer Credit Note',
            'in_invoice': 'Vendor Bill',
            'in_refund': 'Vendor Credit Note',
            'out_receipt': 'Sales Receipt',
            'in_receipt': 'Purchase Receipt',
        }

        # Format for JS
        formatted_moves = []
        for m in recent_moves:
            formatted_moves.append({
                'id': m['id'],
                'name': m['name'],
                'date': m['date'].strftime('%Y-%m-%d') if m['date'] else '',
                'partner': m['partner_id'][1] if m['partner_id'] else 'N/A',
                'amount': m['amount_total'],
                'type': TYPE_MAPPING.get(m['move_type'], str(m['move_type']).replace('_', ' ').title())
            })

        currency_symbol = self.env.company.currency_id.symbol or '$'

        return {
            'cash_balance': cash_balance,
            'receivables': receivables,
            'payables': payables,
            'recent_moves': formatted_moves,
            'currency_symbol': currency_symbol
        }
