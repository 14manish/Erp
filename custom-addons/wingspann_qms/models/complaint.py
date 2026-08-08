# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class QmsComplaint(models.Model):
    _name = 'qms.complaint'
    _description = 'Customer Complaint / Field Issue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_received desc'

    name = fields.Char(
        string='Complaint Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    title = fields.Char(string='Complaint Title', required=True)
    state = fields.Selection([
        ('new', 'New'),
        ('investigating', 'Under Investigation'),
        ('capa_raised', 'CAPA Raised'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string='Status', default='new', tracking=True, required=True)

    complaint_type = fields.Selection([
        ('product_failure', 'Product Failure / Defect'),
        ('performance', 'Performance Issue'),
        ('cosmetic', 'Cosmetic / Aesthetic'),
        ('delivery', 'Delivery / Logistics'),
        ('documentation', 'Documentation Issue'),
        ('other', 'Other'),
    ], string='Complaint Type', required=True, default='product_failure')

    severity = fields.Selection([
        ('critical', 'Critical (Safety)'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Severity', required=True, default='medium', tracking=True)

    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    date_received = fields.Date(string='Date Received', required=True, default=fields.Date.context_today, tracking=True)
    date_resolved = fields.Date(string='Date Resolved', tracking=True)

    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)

    product_id = fields.Many2one('product.product', string='Product Reported')
    lot_id = fields.Many2one('stock.lot', string='Serial / Lot Number')
    invoice_id = fields.Many2one('account.move', string='Related Invoice', domain=[('move_type', '=', 'out_invoice')])
    delivery_id = fields.Many2one('stock.picking', string='Delivery Order')
    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Order')

    complaint_description = fields.Html(string='Complaint Description', required=True)
    customer_expectation = fields.Html(string='Customer Expectation / Resolution Request')
    investigation_notes = fields.Html(string='Investigation Notes')
    resolution = fields.Html(string='Resolution / Response to Customer')

    capa_ids = fields.One2many('qms.capa', 'complaint_id', string='CAPAs')
    ncr_ids = fields.One2many('qms.ncr', 'partner_id', string='Related NCRs',
                               compute='_compute_ncr_ids')
    capa_count = fields.Integer(compute='_compute_counts', string='CAPAs')

    customer_satisfaction = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('partially', 'Partially Satisfied'),
        ('unsatisfied', 'Unsatisfied'),
        ('no_response', 'No Response'),
    ], string='Customer Satisfaction', tracking=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Evidence / Attachments')
    warranty_claim = fields.Boolean(string='Warranty Claim?')
    replacement_issued = fields.Boolean(string='Replacement Issued?')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('qms.complaint') or _('New')
        return super().create(vals_list)

    def _compute_counts(self):
        for rec in self:
            rec.capa_count = len(rec.capa_ids)

    def _compute_ncr_ids(self):
        for rec in self:
            if rec.customer_id:
                rec.ncr_ids = self.env['qms.ncr'].search([('partner_id', '=', rec.customer_id.id)])
            else:
                rec.ncr_ids = self.env['qms.ncr']

    def action_investigate(self):
        self.state = 'investigating'

    def action_raise_capa(self):
        self.state = 'capa_raised'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Raise CAPA',
            'res_model': 'qms.capa',
            'view_mode': 'form',
            'context': {
                'default_complaint_id': self.id,
                'default_title': f'CAPA for Complaint: {self.name}',
                'default_partner_id': self.customer_id.id,
                'default_product_id': self.product_id.id,
            },
        }

    def action_resolve(self):
        self.write({'state': 'resolved', 'date_resolved': fields.Date.context_today(self)})

    def action_close(self):
        self.state = 'closed'

    def action_view_capa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CAPAs',
            'res_model': 'qms.capa',
            'view_mode': 'list,form',
            'domain': [('complaint_id', '=', self.id)],
        }
