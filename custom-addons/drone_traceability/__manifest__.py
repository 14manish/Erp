# -*- coding: utf-8 -*-
{
    'name': "Drone Traceability",
    'summary': """Enhanced tracking for Drone Components and Firmware""",
    'description': """
        Adds custom fields to Inventory Lots/Serial Numbers specifically for Drone Manufacturing.
        Includes Critical Component Tracking and Firmware Versioning.
    """,
    'author': "Krishnashis",
    'category': 'Inventory/Inventory',
    'version': '17.0.1.0.0',
    'depends': ['stock', 'mrp', 'purchase', 'account', 'l10n_in'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'reports/issue_note_report.xml',
        'views/stock_lot_views.xml',
        'views/product_views.xml',
        'views/mrp_bom_views.xml',
        'views/login_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/issue_note_views.xml',
        'views/purchase_order_templates.xml',
        'views/invoice_templates.xml',
        'views/vendor_comparison_views.xml',
        'reports/bom_report.xml',
        'data/drone_demo_data.xml',
    ],
    'installable': True,
    'application': False,
}