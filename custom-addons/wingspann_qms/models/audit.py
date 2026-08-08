# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class QmsAudit(models.Model):
    _name = 'qms.audit'
    _description = 'Quality Audit (Internal / External)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc'

    name = fields.Char(
        string='Audit Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    title = fields.Char(string='Audit Title', required=True)
    audit_type = fields.Selection([
        ('internal', 'Internal Audit'),
        ('external', 'External / Third-Party Audit'),
        ('supplier', 'Supplier Audit'),
        ('customer', 'Customer Audit'),
    ], string='Audit Type', required=True, default='internal', tracking=True)

    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('finding_review', 'Findings Under Review'),
        ('capa_raised', 'CAPA Raised'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='planned', tracking=True)

    standard = fields.Selection([
        ('iso_9001', 'ISO 9001'),
        ('as9100', 'AS9100'),
        ('iatf_16949', 'IATF 16949'),
        ('iso_14001', 'ISO 14001'),
        ('internal', 'Internal Standard'),
        ('other', 'Other'),
    ], string='Standard / Reference', default='internal')

    audit_date = fields.Date(string='Planned Audit Date', required=True, tracking=True)
    audit_end_date = fields.Date(string='Audit End Date', tracking=True)
    close_date = fields.Date(string='Close Date', tracking=True)

    lead_auditor_id = fields.Many2one('res.users', string='Lead Auditor', tracking=True)
    auditee_id = fields.Many2one('res.users', string='Auditee', tracking=True)
    department_id = fields.Many2one('hr.department', string='Audited Department')
    partner_id = fields.Many2one('res.partner', string='External Agency (if applicable)')

    scope = fields.Html(string='Audit Scope / Objectives')
    checklist = fields.Html(string='Audit Checklist / Questions')
    findings = fields.Html(string='Findings Summary', tracking=True)
    conclusion = fields.Html(string='Audit Conclusion')

    finding_ids = fields.One2many('qms.audit.finding', 'audit_id', string='Detailed Findings')
    capa_ids = fields.One2many('qms.capa', 'audit_id', string='CAPAs')
    capa_count = fields.Integer(compute='_compute_counts', string='CAPA Count')
    finding_count = fields.Integer(compute='_compute_counts', string='Finding Count')

    attachment_ids = fields.Many2many('ir.attachment', string='Report / Evidence Attachments')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('qms.audit') or _('New')
        return super().create(vals_list)

    def _compute_counts(self):
        for rec in self:
            rec.capa_count = len(rec.capa_ids)
            rec.finding_count = len(rec.finding_ids)

    def action_start(self):
        self.state = 'in_progress'

    def action_review_findings(self):
        self.state = 'finding_review'

    def action_raise_capa(self):
        self.state = 'capa_raised'

    def action_close(self):
        self.write({'state': 'closed', 'close_date': fields.Date.context_today(self)})

    def action_cancel(self):
        self.state = 'cancelled'

    def action_view_capa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CAPAs',
            'res_model': 'qms.capa',
            'view_mode': 'list,form',
            'domain': [('audit_id', '=', self.id)],
        }

    def action_view_findings(self):
        # We don't have a separate view for findings right now, but returning a simple action is required.
        # Alternatively, returning nothing is fine since findings are inline.
        return True


class QmsAuditFinding(models.Model):
    _name = 'qms.audit.finding'
    _description = 'Audit Finding'

    audit_id = fields.Many2one('qms.audit', string='Audit', required=True, ondelete='cascade')
    finding_type = fields.Selection([
        ('major_nc', 'Major Non-Conformance'),
        ('minor_nc', 'Minor Non-Conformance'),
        ('ofi', 'Opportunity for Improvement'),
        ('observation', 'Observation'),
        ('positive', 'Positive Finding'),
    ], string='Finding Type', required=True, default='minor_nc')
    clause = fields.Char(string='Standard Clause / Requirement')
    description = fields.Text(string='Finding Description', required=True)
    capa_id = fields.Many2one('qms.capa', string='Linked CAPA')
