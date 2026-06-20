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
    'depends': ['stock', 'mrp'],
    'data': [
        'views/stock_lot_views.xml',
        'data/drone_demo_data.xml',
    ],
    'installable': True,
    'application': False,
}
