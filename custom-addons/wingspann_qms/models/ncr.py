# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QmsNcr(models.Model):
    _name = 'qms.ncr'
    _description = 'Non-Conformance Report (NCR)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_detected desc, id desc'

    name = fields.Char(
        string='NCR Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    title = fields.Char(string='Title', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('capa_raised', 'CAPA Raised'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    ncr_type = fields.Selection([
        ('incoming', 'Incoming Material'),
        ('in_process', 'In-Process'),
        ('final', 'Final Inspection'),
        ('field', 'Field / Customer'),
        ('supplier', 'Supplier'),
        ('audit', 'Audit Finding'),
    ], string='NCR Type', required=True, tracking=True)

    severity = fields.Selection([
        ('critical', 'Critical'),
        ('major', 'Major'),
        ('minor', 'Minor'),
        ('observation', 'Observation'),
    ], string='Severity', required=True, default='minor', tracking=True)

    date_detected = fields.Date(string='Date Detected', required=True, default=fields.Date.context_today, tracking=True)
    date_closed = fields.Date(string='Date Closed', tracking=True)

    detected_by = fields.Many2one('res.users', string='Detected By', default=lambda self: self.env.user, tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible Person', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department')

    product_id = fields.Many2one('product.product', string='Product / Component')
    lot_id = fields.Many2one('stock.lot', string='Lot / Serial Number')
    qty_nonconforming = fields.Float(string='Non-Conforming Qty')
    uom_id = fields.Many2one('uom.uom', string='UOM', related='product_id.uom_id')

    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    picking_id = fields.Many2one('stock.picking', string='Receipt / Transfer')
    partner_id = fields.Many2one('res.partner', string='Supplier / Customer')

    description = fields.Html(string='Non-Conformance Description', required=True)
    root_cause = fields.Html(string='Root Cause Analysis')
    immediate_action = fields.Html(string='Immediate / Containment Action')

    capa_ids = fields.One2many('qms.capa', 'ncr_id', string='CAPAs Raised')
    capa_count = fields.Integer(compute='_compute_capa_count', string='CAPA Count')

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    tag_ids = fields.Many2many('qms.tag', string='Tags')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('qms.ncr') or _('New')
        return super().create(vals_list)

    def _compute_capa_count(self):
        for rec in self:
            rec.capa_count = len(rec.capa_ids)

    def action_open(self):
        self.state = 'open'

    def action_under_review(self):
        self.state = 'under_review'

    def action_raise_capa(self):
        self.state = 'capa_raised'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Raise CAPA',
            'res_model': 'qms.capa',
            'view_mode': 'form',
            'context': {
                'default_ncr_id': self.id,
                'default_title': f'CAPA for {self.name}',
                'default_product_id': self.product_id.id,
            },
        }

    def action_close(self):
        self.write({'state': 'closed', 'date_closed': fields.Date.context_today(self)})

    def action_cancel(self):
        self.state = 'cancelled'

    def action_view_capa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CAPAs',
            'res_model': 'qms.capa',
            'view_mode': 'list,form',
            'domain': [('ncr_id', '=', self.id)],
        }


class QmsTag(models.Model):
    _name = 'qms.tag'
    _description = 'QMS Tag'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color')
