# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class QmsSop(models.Model):
    _name = 'qms.sop'
    _description = 'Standard Operating Procedure / Work Instruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Document Title', required=True, tracking=True)
    doc_number = fields.Char(
        string='Document Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    doc_type = fields.Selection([
        ('sop', 'Standard Operating Procedure (SOP)'),
        ('wi', 'Work Instruction (WI)'),
        ('standard', 'Quality Standard'),
        ('form', 'Quality Form / Checklist'),
        ('policy', 'Quality Policy'),
        ('manual', 'Quality Manual'),
        ('other', 'Other'),
    ], string='Document Type', required=True, default='sop', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved / Active'),
        ('obsolete', 'Obsolete'),
    ], string='Status', default='draft', tracking=True, required=True)

    revision = fields.Char(string='Revision', default='Rev 0', tracking=True)
    effective_date = fields.Date(string='Effective Date', tracking=True)
    review_date = fields.Date(string='Next Review Date', tracking=True)

    author_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user)
    reviewer_id = fields.Many2one('res.users', string='Reviewer', tracking=True)
    approver_id = fields.Many2one('res.users', string='Approver', tracking=True)

    department_id = fields.Many2one('hr.department', string='Applicable Department')
    process_id = fields.Many2one('mrp.routing.workcenter', string='Linked MRP Operation')
    product_ids = fields.Many2many('product.template', string='Applicable Products')

    scope = fields.Char(string='Scope / Purpose')
    content = fields.Html(string='Document Content / Procedure Steps')

    attachment_ids = fields.Many2many('ir.attachment', string='Document Files')
    tag_ids = fields.Many2many('qms.tag', string='Tags')

    change_history_ids = fields.One2many('qms.sop.history', 'sop_id', string='Revision History')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('doc_number', _('New')) == _('New'):
                vals['doc_number'] = self.env['ir.sequence'].next_by_code('qms.sop') or _('New')
        return super().create(vals_list)

    def action_submit_review(self):
        self.state = 'review'

    def action_approve(self):
        self.write({
            'state': 'approved',
            'effective_date': fields.Date.context_today(self),
        })
        # Log revision history
        self.env['qms.sop.history'].create({
            'sop_id': self.id,
            'revision': self.revision,
            'date': fields.Date.context_today(self),
            'approved_by': self.env.user.id,
            'change_summary': f'Approved - {self.revision}',
        })

    def action_obsolete(self):
        self.state = 'obsolete'

    def action_new_revision(self):
        self.ensure_one()
        new_sop = self.copy({
            'state': 'draft',
            'effective_date': False,
            'revision': f'Rev {(int(self.revision.split()[-1]) + 1) if self.revision else 1}',
        })
        self.action_obsolete()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qms.sop',
            'res_id': new_sop.id,
            'view_mode': 'form',
        }


class QmsSopHistory(models.Model):
    _name = 'qms.sop.history'
    _description = 'SOP Revision History'
    _order = 'date desc'

    sop_id = fields.Many2one('qms.sop', string='Document', required=True, ondelete='cascade')
    revision = fields.Char(string='Revision')
    date = fields.Date(string='Date')
    approved_by = fields.Many2one('res.users', string='Approved By')
    change_summary = fields.Text(string='Change Summary')
