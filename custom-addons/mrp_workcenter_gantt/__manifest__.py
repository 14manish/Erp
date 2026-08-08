{
    'name': 'MRP Work Center Gantt View',
    'version': '17.0.1.0.0',
    'summary': 'Interactive Gantt chart for Work Center scheduling in Manufacturing',
    'description': """
        Adds a fully interactive Gantt chart view to the Manufacturing Operations menu.
        Shows all work orders per work center on a visual timeline.
        Supports drag-and-drop rescheduling, zoom levels (Day / Week / Month),
        and color-coded job status indicators.
    """,
    'author': 'Wingspann',
    'license': 'LGPL-3',
    'category': 'Manufacturing',
    'depends': ['mrp'],
    'data': [
        'views/mrp_production_views.xml',
        'views/actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_workcenter_gantt/static/src/gantt_action.xml',
            'mrp_workcenter_gantt/static/src/gantt_action.js',
            'mrp_workcenter_gantt/static/src/gantt.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
