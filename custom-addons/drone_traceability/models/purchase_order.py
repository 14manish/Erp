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

    x_po_prefix = fields.Char(string="PO Prefix", compute='_compute_x_po_prefix')
    x_po_number_suffix = fields.Char(string="PO Number", compute='_compute_x_po_suffix', inverse='_inverse_x_po_suffix', store=True)

    @api.depends('date_order')
    def _compute_x_po_prefix(self):
        for po in self:
            date_order = po.date_order or fields.Datetime.now()
            if isinstance(date_order, str):
                date_order = fields.Datetime.from_string(date_order)
            year = date_order.year
            if date_order.month < 4:
                fy = f"{year - 1}-{str(year)[-2:]}"
            else:
                fy = f"{year}-{str(year + 1)[-2:]}"
            po.x_po_prefix = f"WSGPL/{fy}/"

    @api.depends('name', 'x_po_prefix')
    def _compute_x_po_suffix(self):
        for po in self:
            if po.name and po.name != 'New' and po.x_po_prefix and po.name.startswith(po.x_po_prefix):
                po.x_po_number_suffix = po.name.split('/')[-1]
            else:
                po.x_po_number_suffix = po.x_po_number_suffix or ''

    def _inverse_x_po_suffix(self):
        for po in self:
            if po.x_po_prefix and po.x_po_number_suffix:
                po.name = po.x_po_prefix + po.x_po_number_suffix

    @api.onchange('x_po_number_suffix')
    def _onchange_x_po_number_suffix_validation(self):
        for po in self:
            if po.x_po_number_suffix:
                cleaned = ''.join(filter(str.isdigit, po.x_po_number_suffix))
                if cleaned != po.x_po_number_suffix:
                    po.x_po_number_suffix = cleaned

    from odoo.exceptions import ValidationError

    @api.constrains('x_po_number_suffix')
    def _check_po_number_suffix(self):
        for po in self:
            if po.x_po_number_suffix:
                if not po.x_po_number_suffix.isdigit():
                    raise ValidationError("The PO Number suffix must contain only positive numbers without any spaces or special characters.")

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
