# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class AccountDashboard(models.TransientModel):
    _name = 'wingspann.accounting.dashboard'
    _description = 'Financial Dashboard Analytics'

    # ─────────────────────────────────────────────────────────────────
    # BUDGET DASHBOARD (new)
    # ─────────────────────────────────────────────────────────────────
    @api.model
    def set_allocated_budget(self, value):
        """Save the allocated budget to a persistent system parameter."""
        self.env['ir.config_parameter'].sudo().set_param(
            'wingspann.budget.allocated', str(float(value))
        )
        return True

    @api.model
    def get_budget_dashboard_data(self):
        company_id = self.env.company.id
        currency_symbol = self.env.company.currency_id.symbol or '₹'

        # ── Indian Financial Year (April → March) ────────────────────
        today = date.today()
        if today.month >= 4:
            fy_start = date(today.year, 4, 1)
            fy_end   = date(today.year + 1, 3, 31)
            fy_label = f"FY {today.year}-{str(today.year + 1)[2:]}"
        else:
            fy_start = date(today.year - 1, 4, 1)
            fy_end   = date(today.year, 3, 31)
            fy_label = f"FY {today.year - 1}-{str(today.year)[2:]}"

        # ── Allocated Budget (configurable via Settings → Parameters) ─
        icp = self.env['ir.config_parameter'].sudo()
        try:
            allocated_budget = float(
                icp.get_param('wingspann.budget.allocated', default='1000000')
            )
        except (ValueError, TypeError):
            allocated_budget = 1_000_000.0

        # ── Total Expenses from posted Vendor Bills (current FY) ──────
        self.env.cr.execute("""
            SELECT COALESCE(SUM(am.amount_total), 0.0)
            FROM account_move am
            WHERE am.move_type = 'in_invoice'
              AND am.state     = 'posted'
              AND am.company_id = %s
              AND am.invoice_date >= %s
              AND am.invoice_date <= %s
        """, (company_id, fy_start, fy_end))
        row = self.env.cr.fetchone()
        total_expenses = float(row[0]) if row and row[0] else 0.0

        # ── Expense Breakdown by Account (current FY) ─────────────────
        self.env.cr.execute("""
            SELECT
                aa.name    AS account_name,
                aa.code    AS account_code,
                COALESCE(SUM(aml.debit), 0.0) AS amount
            FROM account_move_line aml
            JOIN account_move    am  ON aml.move_id    = am.id
            JOIN account_account aa  ON aml.account_id = aa.id
            WHERE am.move_type    = 'in_invoice'
              AND am.state        = 'posted'
              AND am.company_id   = %s
              AND am.invoice_date >= %s
              AND am.invoice_date <= %s
              AND aa.account_type LIKE 'expense%%'
            GROUP BY aa.id, aa.name, aa.code
            ORDER BY amount DESC
        """, (company_id, fy_start, fy_end))
        expense_rows = self.env.cr.dictfetchall()

        # Keyword → Category mapping
        categories = [
            {
                'name': 'Manpower',
                'icon': 'fa-users',
                'amount': 0.0,
                'keywords': [
                    'salary', 'wage', 'manpower', 'labour', 'labor',
                    'employee', 'staff', 'payroll', 'bonus', 'incentive',
                    'pf', 'esic', 'gratuity', 'overtime',
                ],
            },
            {
                'name': 'Goods & Inventory',
                'icon': 'fa-cube',
                'amount': 0.0,
                'keywords': [
                    'goods', 'inventory', 'material', 'stock', 'supply',
                    'raw', 'component', 'parts', 'purchase', 'procurement',
                    'consumable',
                ],
            },
            {
                'name': 'Electricity & Utilities',
                'icon': 'fa-bolt',
                'amount': 0.0,
                'keywords': [
                    'electricity', 'utility', 'utilities', 'power', 'water',
                    'gas', 'fuel', 'telecom', 'internet', 'telephone',
                    'broadband', 'mobile',
                ],
            },
            {
                'name': 'Rent & Facilities',
                'icon': 'fa-building',
                'amount': 0.0,
                'keywords': [
                    'rent', 'lease', 'facility', 'office', 'building',
                    'premise', 'maintenance', 'repair',
                ],
            },
            {
                'name': 'Others',
                'icon': 'fa-ellipsis-h',
                'amount': 0.0,
                'keywords': [],  # catch-all
            },
        ]

        for row in expense_rows:
            name_lower = str(row.get('account_name', '')).lower()
            matched = False
            for cat in categories[:-1]:   # skip Others in loop
                if any(kw in name_lower for kw in cat['keywords']):
                    cat['amount'] += float(row['amount'])
                    matched = True
                    break
            if not matched:
                categories[-1]['amount'] += float(row['amount'])

        # Only return categories that have non-zero amounts (keep Others if needed)
        non_zero = [c for c in categories if c['amount'] > 0]
        expense_categories = non_zero if non_zero else [
            {'name': 'No expenses recorded', 'icon': 'fa-info-circle', 'amount': 0.0}
        ]

        remaining_balance = max(allocated_budget - total_expenses, 0.0)

        # ── PO Commitments (confirmed, not fully billed) ───────────────
        self.env.cr.execute("""
            SELECT COALESCE(SUM(po.amount_total), 0.0)
            FROM purchase_order po
            WHERE po.state       = 'purchase'
              AND po.company_id  = %s
              AND (po.invoice_status IS NULL OR po.invoice_status != 'invoiced')
        """, (company_id,))
        row = self.env.cr.fetchone()
        po_commitment = float(row[0]) if row and row[0] else 0.0

        # ── PR Commitments proxy (draft / sent RFQs) ──────────────────
        self.env.cr.execute("""
            SELECT COALESCE(SUM(po.amount_total), 0.0)
            FROM purchase_order po
            WHERE po.state      IN ('draft', 'sent')
              AND po.company_id  = %s
        """, (company_id,))
        row = self.env.cr.fetchone()
        pr_commitment = float(row[0]) if row and row[0] else 0.0

        return {
            'allocated_budget':   allocated_budget,
            'total_expenses':     total_expenses,
            'remaining_balance':  remaining_balance,
            'expense_categories': expense_categories,
            'po_commitment':      po_commitment,
            'pr_commitment':      pr_commitment,
            'currency_symbol':    currency_symbol,
            'fy_label':           fy_label,
        }

    # ─────────────────────────────────────────────────────────────────
    # LEGACY ACCOUNTING DASHBOARD (unchanged)
    # ─────────────────────────────────────────────────────────────────
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

        # Receivables
        self.env.cr.execute("""
            SELECT SUM(amount_residual) FROM account_move
            WHERE move_type = 'out_invoice' AND state = 'posted'
              AND payment_state IN ('not_paid', 'partial')
              AND company_id = %s
        """, (company_id,))
        res = self.env.cr.fetchone()
        receivables = res[0] if res and res[0] else 0.0

        # Payables
        self.env.cr.execute("""
            SELECT SUM(amount_residual) FROM account_move
            WHERE move_type = 'in_invoice' AND state = 'posted'
              AND payment_state IN ('not_paid', 'partial')
              AND company_id = %s
        """, (company_id,))
        res = self.env.cr.fetchone()
        payables = res[0] if res and res[0] else 0.0

        # Recent Activity
        recent_moves = self.env['account.move'].search_read(
            [('state', '=', 'posted'), ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount_total', 'move_type', 'state'],
            limit=10, order='date desc, id desc'
        )

        TYPE_MAPPING = {
            'entry':       'Journal Entry',
            'out_invoice': 'Customer Invoice',
            'out_refund':  'Customer Credit Note',
            'in_invoice':  'Vendor Bill',
            'in_refund':   'Vendor Credit Note',
            'out_receipt': 'Sales Receipt',
            'in_receipt':  'Purchase Receipt',
        }

        formatted_moves = []
        for m in recent_moves:
            formatted_moves.append({
                'id':      m['id'],
                'name':    m['name'],
                'date':    m['date'].strftime('%Y-%m-%d') if m['date'] else '',
                'partner': m['partner_id'][1] if m['partner_id'] else 'N/A',
                'amount':  m['amount_total'],
                'type':    TYPE_MAPPING.get(m['move_type'],
                                            str(m['move_type']).replace('_', ' ').title()),
            })

        currency_symbol = self.env.company.currency_id.symbol or '₹'
        today = fields.Date.context_today(self)
        start_of_week  = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Incoming Payments
        domain_in_month = [('payment_type', '=', 'inbound'), ('state', '=', 'posted'),
                           ('company_id', '=', company_id), ('date', '>=', start_of_month)]
        res_in_month = self.env['account.payment'].read_group(domain_in_month, ['amount:sum'], [])
        incoming_monthly = res_in_month[0]['amount'] if res_in_month and res_in_month[0].get('amount') else 0.0

        domain_in_week = [('payment_type', '=', 'inbound'), ('state', '=', 'posted'),
                          ('company_id', '=', company_id), ('date', '>=', start_of_week)]
        res_in_week = self.env['account.payment'].read_group(domain_in_week, ['amount:sum'], [])
        incoming_weekly = res_in_week[0]['amount'] if res_in_week and res_in_week[0].get('amount') else 0.0

        recent_incoming = self.env['account.payment'].search_read(
            [('payment_type', '=', 'inbound'), ('state', '=', 'posted'),
             ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount'], limit=5, order='date desc, id desc'
        )
        for r in recent_incoming:
            r['date']    = r['date'].strftime('%Y-%m-%d') if r['date'] else ''
            r['partner'] = r['partner_id'][1] if r['partner_id'] else 'N/A'

        # Outgoing Payments
        domain_out_month = [('payment_type', '=', 'outbound'), ('state', '=', 'posted'),
                            ('company_id', '=', company_id), ('date', '>=', start_of_month)]
        res_out_month = self.env['account.payment'].read_group(domain_out_month, ['amount:sum'], [])
        outgoing_monthly = res_out_month[0]['amount'] if res_out_month and res_out_month[0].get('amount') else 0.0

        domain_out_week = [('payment_type', '=', 'outbound'), ('state', '=', 'posted'),
                           ('company_id', '=', company_id), ('date', '>=', start_of_week)]
        res_out_week = self.env['account.payment'].read_group(domain_out_week, ['amount:sum'], [])
        outgoing_weekly = res_out_week[0]['amount'] if res_out_week and res_out_week[0].get('amount') else 0.0

        recent_outgoing = self.env['account.payment'].search_read(
            [('payment_type', '=', 'outbound'), ('state', '=', 'posted'),
             ('company_id', '=', company_id)],
            ['name', 'date', 'partner_id', 'amount'], limit=5, order='date desc, id desc'
        )
        for r in recent_outgoing:
            r['date']    = r['date'].strftime('%Y-%m-%d') if r['date'] else ''
            r['partner'] = r['partner_id'][1] if r['partner_id'] else 'N/A'

        return {
            'cash_balance':      cash_balance,
            'receivables':       receivables,
            'payables':          payables,
            'recent_moves':      formatted_moves,
            'currency_symbol':   currency_symbol,
            'incoming_monthly':  incoming_monthly,
            'incoming_weekly':   incoming_weekly,
            'recent_incoming':   recent_incoming,
            'outgoing_monthly':  outgoing_monthly,
            'outgoing_weekly':   outgoing_weekly,
            'recent_outgoing':   recent_outgoing,
        }
