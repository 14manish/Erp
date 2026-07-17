# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    flight_test_status = fields.Selection([
        ('untested', 'Untested'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], string="Flight Test Status", default='untested', tracking=True)

    product_serial_no = fields.Char(string="Product Serial No", help="Unique manufacturer serial number or part number for this component.")
    model = fields.Char(string="Model", help="Make or model name/number.")
    version = fields.Char(string="Version", help="Hardware or software version.")
    
    component_trader = fields.Char(string="Component Trader", help="Vendor or trader name.")
    country_of_origin = fields.Char(string="Country of Origin", help="Country where the component was manufactured.")
    product_link = fields.Char(string="Product Link", help="URL or link to the product.")
