# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_serial_no = fields.Char(related='product_id.product_serial_no', string="Product Serial No", readonly=False)
    model = fields.Char(related='product_id.model', string="Model", readonly=False)
    version = fields.Char(related='product_id.version', string="Version", readonly=False)
    component_trader = fields.Char(related='product_id.component_trader', string="Component Trader", readonly=False)
    country_of_origin = fields.Char(related='product_id.country_of_origin', string="Country of Origin", readonly=False)
    product_link = fields.Char(related='product_id.product_link', string="Product Link", readonly=False)
    
    # We will use the product's standard price for unit price
    unit_price = fields.Float(related='product_id.standard_price', string="Unit Price", readonly=False)
    
    # We'll use the product's weight
    weight = fields.Float(related='product_id.weight', string="Weight", readonly=False)
    
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=False)

    @api.depends('product_qty', 'unit_price')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.product_qty * line.unit_price
