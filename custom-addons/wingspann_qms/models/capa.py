# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class QmsCapa(models.Model):
    _name = 'qms.capa'
    _description = 'Corrective and Preventive Action (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'target_date asc, id desc'

    name = fields.Char(
        string='CAPA Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    title = fields.Char(string='Title', required=True, tracking=True)
    capa_type = fields.Selection([
        ('corrective', 'Corrective Action (CA)'),
        ('preventive', 'Preventive Action (PA)'),
    ], string='Type', required=True, default='corrective', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'In Progress'),
        ('verification', 'Pending Verification'),
        ('effective', 'Verified Effective'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Very High'),
        ('3', 'Critical'),
    ], string='Priority', default='0')

    ncr_id = fields.Many2one('qms.ncr', string='Source NCR', tracking=True)
    audit_id = fields.Many2one('qms.audit', string='Source Audit', tracking=True)
    complaint_id = fields.Many2one('qms.complaint', string='Source Complaint', tracking=True)

    product_id = fields.Many2one('product.product', string='Affected Product')
    partner_id = fields.Many2one('res.partner', string='Supplier / Customer')
    department_id = fields.Many2one('hr.department', string='Department')

    responsible_id = fields.Many2one('res.users', string='Responsible Person', required=True,
                                      default=lambda self: self.env.user, tracking=True)
    approver_id = fields.Many2one('res.users', string='Approver / Reviewer', tracking=True)
    created_by = fields.Many2one('res.users', string='Raised By', default=lambda self: self.env.user, readonly=True)

    date_raised = fields.Date(string='Date Raised', default=fields.Date.context_today, required=True)
    target_date = fields.Date(string='Target Completion Date', required=True, tracking=True)
    date_verified = fields.Date(string='Date Verified', tracking=True)
    date_closed = fields.Date(string='Date Closed', tracking=True)

    root_cause = fields.Html(string='Root Cause Analysis', required=True)
    action_description = fields.Html(string='Action Plan / Description', required=True)
    effectiveness_criteria = fields.Html(string='Effectiveness Criteria')
    verification_notes = fields.Html(string='Verification Notes')

    is_overdue = fields.Boolean(compute='_compute_overdue', string='Overdue', store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('qms.capa') or _('New')
        return super().create(vals_list)

    @api.depends('target_date', 'state')
    def _compute_overdue(self):
        today = date.today()
        for rec in self:
            rec.is_overdue = (
                rec.target_date
                and rec.target_date < today
                and rec.state not in ('closed', 'cancelled', 'effective')
            )

    def action_start(self):
        self.state = 'open'

    def action_pending_verification(self):
        self.state = 'verification'

    def action_verify_effective(self):
        self.write({'state': 'effective', 'date_verified': fields.Date.context_today(self)})

    def action_close(self):
        self.write({'state': 'closed', 'date_closed': fields.Date.context_today(self)})

    def action_cancel(self):
        self.state = 'cancelled'
