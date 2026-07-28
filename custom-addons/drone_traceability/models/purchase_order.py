# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_quotation_ref = fields.Char(string="Your Quotation No")
    x_quotation_date = fields.Date(string="Quotation Date")
    x_kind_attn = fields.Char(string="Kind Attn")
    @api.model
    def default_get(self, fields_list):
        res = super(PurchaseOrder, self).default_get(fields_list)
        if 'name' in fields_list and res.get('name', 'New') == 'New':
            seq = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
            if '[FY]' in seq:
                date_order = res.get('date_order') or fields.Datetime.now()
                if isinstance(date_order, str):
                    date_order = fields.Datetime.from_string(date_order)
                year = date_order.year
                if date_order.month < 4:
                    fy = f"{year - 1}-{str(year)[-2:]}"
                else:
                    fy = f"{year}-{str(year + 1)[-2:]}"
                seq = seq.replace('[FY]', fy)
            res['name'] = seq
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                # Let standard sequence engine generate the number first, using a placeholder [FY]
                date_order = vals.get('date_order') or fields.Datetime.now()
                if isinstance(date_order, str):
                    date_order = fields.Datetime.from_string(date_order)
                
                seq = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
                
                if '[FY]' in seq:
                    year = date_order.year
                    if date_order.month < 4:
                        fy = f"{year - 1}-{str(year)[-2:]}"
                    else:
                        fy = f"{year}-{str(year + 1)[-2:]}"
                    seq = seq.replace('[FY]', fy)
                    
                vals['name'] = seq
                
        return super(PurchaseOrder, self).create(vals_list)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_hsn_code = fields.Char(string="HSN/SAC", compute="_compute_x_hsn_code", store=True, readonly=False)

    @api.depends('product_id')
    def _compute_x_hsn_code(self):
        for line in self:
            line.x_hsn_code = line.product_id.l10n_in_hsn_code or line.product_id.product_tmpl_id.l10n_in_hsn_code or ''

    def action_compare_vendors(self):
        self.ensure_one()
        if not self.product_id:
            return

        # Fetch supplier info for this product
        supplier_infos = self.env['product.supplierinfo'].search([
            '|',
            ('product_id', '=', self.product_id.id),
            '&',
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('product_id', '=', False)
        ])

        # Prepare wizard lines
        wizard_lines = []
        for supplier in supplier_infos:
            wizard_lines.append((0, 0, {
                'partner_id': supplier.partner_id.id,
                'min_qty': supplier.min_qty,
                'price': supplier.price,
                'currency_id': supplier.currency_id.id,
                'delay': supplier.delay,
            }))

        wizard = self.env['vendor.comparison.wizard'].create({
            'po_line_id': self.id,
            'product_id': self.product_id.id,
            'line_ids': wizard_lines,
        })

        return {
            'name': 'Compare Vendors',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'vendor.comparison.wizard',
            'res_id': wizard.id,
            'target': 'new',
        }
