# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

        # Analytics for Payments (Weekly and Monthly)
        today = fields.Date.context_today(self)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Incoming Payments (Receivables Analytics)
        domain_in_month = [('payment_type', '=', 'inbound'), ('state', '=', 'posted'), ('company_id', '=', company_id), ('date', '>=', start_of_month)]
        res_in_month = self.env['account.payment'].read_group(domain_in_month, ['amount:sum'], [])
        incoming_monthly = res_in_month[0]['amount'] if res_in_month and res_in_month[0].get('amount') else 0.0

        domain_in_week = [('payment_type', '=', 'inbound'), ('state', '=', 'posted'), ('company_id', '=', company_id), ('date', '>=', start_of_week)]
        res_in_week = self.env['account.payment'].read_group(domain_in_week, ['amount:sum'], [])
        incoming_weekly = res_in_week[0]['amount'] if res_in_week and res_in_week[0].get('amount') else 0.0

        recent_incoming = self.env['account.payment'].search_read(
            [('payment_type', '=', 'inbound'), ('state', '=', 'posted'), ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount'], limit=5, order='date desc, id desc'
        )
        for r in recent_incoming:
            r['date'] = r['date'].strftime('%Y-%m-%d') if r['date'] else ''
            r['partner'] = r['partner_id'][1] if r['partner_id'] else 'N/A'

        # Outgoing Payments (Payables Analytics)
        domain_out_month = [('payment_type', '=', 'outbound'), ('state', '=', 'posted'), ('company_id', '=', company_id), ('date', '>=', start_of_month)]
        res_out_month = self.env['account.payment'].read_group(domain_out_month, ['amount:sum'], [])
        outgoing_monthly = res_out_month[0]['amount'] if res_out_month and res_out_month[0].get('amount') else 0.0

        domain_out_week = [('payment_type', '=', 'outbound'), ('state', '=', 'posted'), ('company_id', '=', company_id), ('date', '>=', start_of_week)]
        res_out_week = self.env['account.payment'].read_group(domain_out_week, ['amount:sum'], [])
        outgoing_weekly = res_out_week[0]['amount'] if res_out_week and res_out_week[0].get('amount') else 0.0

        recent_outgoing = self.env['account.payment'].search_read(
            [('payment_type', '=', 'outbound'), ('state', '=', 'posted'), ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount'], limit=5, order='date desc, id desc'
        )
        for r in recent_outgoing:
            r['date'] = r['date'].strftime('%Y-%m-%d') if r['date'] else ''
            r['partner'] = r['partner_id'][1] if r['partner_id'] else 'N/A'

        return {
            'cash_balance': cash_balance,
            'receivables': receivables,
            'payables': payables,
            'recent_moves': formatted_moves,
            'currency_symbol': currency_symbol,
            'incoming_monthly': incoming_monthly,
            'incoming_weekly': incoming_weekly,
            'recent_incoming': recent_incoming,
            'outgoing_monthly': outgoing_monthly,
            'outgoing_weekly': outgoing_weekly,
            'recent_outgoing': recent_outgoing,
        }
