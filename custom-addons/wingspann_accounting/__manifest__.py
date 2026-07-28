# -*- coding: utf-8 -*-
{
    'name': "Wingspann Custom Accounting",
    'summary': """Core Accounting Menus, Financial Dashboard, and Reports tailored for Wingspann""",
    'description': """
        Unlocks Odoo Community Accounting features:
        - Financial Dashboard
        - Journal Entries & Items
        - Chart of Accounts, Journals, Taxes
        - General Ledger & Partner Ledger PDF Reports
    """,
    'author': "Wingspann Global",
    'category': 'Accounting/Localizations',
    'version': '17.0.1.0.0',
    'depends': ['account', 'web', 'l10n_in'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/accounting_menu_views.xml',
        'wizard/general_ledger_wizard_views.xml',
        'wizard/partner_ledger_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/general_ledger_template.xml',
        'reports/partner_ledger_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wingspann_accounting/static/src/css/dashboard.css',
            'wingspann_accounting/static/src/js/dashboard.js',
            'wingspann_accounting/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
