# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InventoryIssueNote(models.Model):
    _name = 'inventory.issue.note'
    _description = 'Inventory Material Issue & Return Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Requisition No.', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New')
    )
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today,
        tracking=True
    )
    indented_by_id = fields.Many2one(
        'res.users', string='Indented By', default=lambda self: self.env.user,
        required=True, tracking=True
    )
    issued_by_id = fields.Many2one(
        'res.users', string='Issued By', readonly=True, tracking=True
    )
    authorized_by_id = fields.Many2one(
        'res.users', string='Authorized By', readonly=True, tracking=True
    )
    for_use_at = fields.Char(
        string='For Use At', required=True, tracking=True,
        help="Location, Project, or Work Center where items will be used"
    )
    notes = fields.Text(string='Notes / Special Instructions')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company
    )
    line_ids = fields.One2many(
        'inventory.issue.note.line', 'issue_note_id', string='Item Lines', copy=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inventory.issue.note') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("Please add at least one item line before submitting."))
            rec.state = 'to_approve'

    def action_approve(self):
        for rec in self:
            rec.authorized_by_id = self.env.user
            rec.state = 'approved'

    def action_issue(self):
        for rec in self:
            rec.issued_by_id = self.env.user
            for line in rec.line_ids:
                if line.qty_issued <= 0:
                    line.qty_issued = line.qty_required
            rec.state = 'issued'

    def action_return(self):
        for rec in self:
            for line in rec.line_ids:
                if line.qty_returned <= 0:
                    line.qty_returned = line.qty_issued
            rec.state = 'returned'

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})


class InventoryIssueNoteLine(models.Model):
    _name = 'inventory.issue.note.line'
    _description = 'Inventory Material Issue Note Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sr. No.', default=10)
    issue_note_id = fields.Many2one(
        'inventory.issue.note', string='Issue Note Reference',
        ondelete='cascade', required=True
    )
    product_id = fields.Many2one(
        'product.product', string='Product / Item', required=True
    )
    product_code = fields.Char(
        string='Material Code', related='product_id.default_code', readonly=True
    )
    description = fields.Char(string='Item Description', required=True)
    purpose = fields.Char(string='Purpose')
    qty_required = fields.Float(string='Quantity Required', default=1.0, digits='Product Unit of Measure')
    qty_issued = fields.Float(string='Quantity Issued', default=0.0, digits='Product Unit of Measure')
    qty_returned = fields.Float(string='Quantity Returned', default=0.0, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unit of Measure', related='product_id.uom_id', readonly=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.display_name
            if not self.product_code:
                self.product_code = self.product_id.default_code
