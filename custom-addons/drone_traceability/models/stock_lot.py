# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Custom Drone Specific Fields
    is_critical_component = fields.Boolean(
        string='Critical Component',
        help='Check if this component is flight-critical and requires strict quality control.',
        default=False
    )
    firmware_version = fields.Char(
        string='Firmware Version',
        help='Version of the firmware flashed onto this component (if applicable).'
    )
    compliance_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved for Flight'),
        ('rejected', 'Rejected/Quarantine')
    ], string='Compliance Status', default='pending', tracking=True)
