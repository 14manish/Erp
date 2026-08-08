# -*- coding: utf-8 -*-
{
    'name': 'Wingspann Quality Management System',
    'version': '17.0.1.0.0',
    'summary': 'Comprehensive QMS for Wingspann Global Drone Manufacturing',
    'description': """
        Full Quality Management System including:
        - Non-Conformance Reports (NCR)
        - Corrective & Preventive Actions (CAPA)
        - Equipment Calibration Tracking
        - Document Control (SOPs & Work Instructions)
        - Audit Management (Internal & External)
        - Customer Complaints & Field Issues
        - QMS Dashboard with KPIs
    """,
    'category': 'Quality',
    'author': 'Wingspann Global',
    'website': 'https://wingspann.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'stock',
        'mrp',
        'purchase',
        'account',
        'drone_traceability',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/qms_sequence_data.xml',
        'views/ncr_views.xml',
        'views/capa_views.xml',
        'views/calibration_views.xml',
        'views/sop_views.xml',
        'views/audit_views.xml',
        'views/complaint_views.xml',
        'views/qms_dashboard_views.xml',
        'views/qms_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wingspann_qms/static/src/css/qms_dashboard.css',
            'wingspann_qms/static/src/xml/qms_dashboard.xml',
            'wingspann_qms/static/src/js/qms_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
