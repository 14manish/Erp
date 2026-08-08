# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta


class QmsEquipmentCalibration(models.Model):
    _name = 'qms.calibration'
    _description = 'Equipment Calibration Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'next_calibration_date asc'

    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    equipment_code = fields.Char(
        string='Equipment Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    state = fields.Selection([
        ('active', 'Active / In Service'),
        ('calibrated', 'Calibrated'),
        ('overdue', 'Calibration Overdue'),
        ('in_calibration', 'Sent for Calibration'),
        ('retired', 'Retired'),
    ], string='Status', default='active', tracking=True)

    equipment_type = fields.Selection([
        ('measurement', 'Measurement Tool'),
        ('test_equipment', 'Test Equipment'),
        ('jig_fixture', 'Jig / Fixture'),
        ('gauge', 'Gauge'),
        ('other', 'Other'),
    ], string='Equipment Type', required=True, default='measurement')

    location = fields.Char(string='Location / Lab')
    department_id = fields.Many2one('hr.department', string='Department')
    responsible_id = fields.Many2one('res.users', string='Custodian', tracking=True)

    manufacturer = fields.Char(string='Manufacturer / Make')
    model_number = fields.Char(string='Model Number')
    serial_number = fields.Char(string='Serial Number')
    measurement_range = fields.Char(string='Measurement Range')
    accuracy = fields.Char(string='Accuracy / Tolerance')

    last_calibration_date = fields.Date(string='Last Calibration Date', tracking=True)
    calibration_frequency = fields.Integer(string='Calibration Frequency (Days)', default=365)
    next_calibration_date = fields.Date(
        string='Next Calibration Due',
        compute='_compute_next_calibration',
        store=True,
        tracking=True,
    )
    calibration_agency = fields.Char(string='Calibrating Agency / Lab')
    calibration_certificate = fields.Char(string='Certificate Number')

    is_overdue = fields.Boolean(compute='_compute_overdue', string='Overdue', store=True)
    days_until_due = fields.Integer(compute='_compute_days_until_due', string='Days Until Due')

    history_ids = fields.One2many('qms.calibration.history', 'calibration_id', string='Calibration History')
    attachment_ids = fields.Many2many('ir.attachment', string='Certificates / Attachments')
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('equipment_code', _('New')) == _('New'):
                vals['equipment_code'] = self.env['ir.sequence'].next_by_code('qms.calibration') or _('New')
        return super().create(vals_list)

    @api.depends('last_calibration_date', 'calibration_frequency')
    def _compute_next_calibration(self):
        for rec in self:
            if rec.last_calibration_date and rec.calibration_frequency:
                rec.next_calibration_date = rec.last_calibration_date + timedelta(days=rec.calibration_frequency)
            else:
                rec.next_calibration_date = False

    @api.depends('next_calibration_date', 'state')
    def _compute_overdue(self):
        today = date.today()
        for rec in self:
            rec.is_overdue = (
                rec.next_calibration_date
                and rec.next_calibration_date < today
                and rec.state not in ('retired', 'in_calibration')
            )

    @api.depends('next_calibration_date')
    def _compute_days_until_due(self):
        today = date.today()
        for rec in self:
            if rec.next_calibration_date:
                rec.days_until_due = (rec.next_calibration_date - today).days
            else:
                rec.days_until_due = 0

    def action_send_for_calibration(self):
        self.state = 'in_calibration'

    def action_calibration_done(self):
        self.write({
            'state': 'calibrated',
            'last_calibration_date': fields.Date.context_today(self),
        })
        # Log history
        self.env['qms.calibration.history'].create({
            'calibration_id': self.id,
            'date': fields.Date.context_today(self),
            'performed_by': self.env.user.id,
            'agency': self.calibration_agency,
        })

    def action_retire(self):
        self.state = 'retired'


class QmsCalibrationHistory(models.Model):
    _name = 'qms.calibration.history'
    _description = 'Calibration History Log'
    _order = 'date desc'

    calibration_id = fields.Many2one('qms.calibration', string='Equipment', required=True, ondelete='cascade')
    date = fields.Date(string='Calibration Date', required=True)
    performed_by = fields.Many2one('res.users', string='Performed By')
    agency = fields.Char(string='Agency / Lab')
    certificate_no = fields.Char(string='Certificate Number')
    result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail'), ('conditional', 'Conditional')], default='pass')
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Certificates')
