# -*- coding: utf-8 -*-
from odoo import models, fields, api

class VendorComparisonWizard(models.TransientModel):
    _name = 'vendor.comparison.wizard'
    _description = 'Vendor Comparison Wizard'

    po_line_id = fields.Many2one('purchase.order.line', string='PO Line', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    line_ids = fields.One2many('vendor.comparison.line', 'wizard_id', string='Vendors')

class VendorComparisonLine(models.TransientModel):
    _name = 'vendor.comparison.line'
    _description = 'Vendor Comparison Line'

    wizard_id = fields.Many2one('vendor.comparison.wizard', string='Wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    min_qty = fields.Float(string='Min. Qty', readonly=True)
    price = fields.Float(string='Price', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    delay = fields.Integer(string='Delivery Lead Time (days)', readonly=True)
    
    def action_use_price(self):
        """Update the PO line price to this vendor's price and change the PO vendor."""
        self.ensure_one()
        if self.wizard_id.po_line_id:
            # Change the PO line price
            self.wizard_id.po_line_id.price_unit = self.price
            # Change the entire Purchase Order's vendor
            self.wizard_id.po_line_id.order_id.partner_id = self.partner_id
        return {'type': 'ir.actions.act_window_close'}
