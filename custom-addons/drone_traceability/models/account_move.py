# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    x_ewaybill_no = fields.Char(string="e-Way Bill No", copy=False)
    x_ewaybill_date = fields.Date(string="e-Way Bill Date", copy=False)
    x_transporter_name = fields.Char(string="Transporter Name")
    x_vehicle_no = fields.Char(string="Vehicle / Trans Doc No")
    x_transportation_address = fields.Char(string="Transportation Address")
    x_transport_doc_no = fields.Char(string="Document No.")
    x_transport_doc_date = fields.Date(string="Document Date")
    x_transaction_type = fields.Selection([
        ('Regular', 'Regular'),
        ('Bill To - Ship To', 'Bill To - Ship To'),
        ('Bill From - Dispatch From', 'Bill From - Dispatch From'),
        ('Transit', 'Transit')
    ], string="Transaction Type", default='Regular')
    x_reason_for_transport = fields.Selection([
        ('Outward - Supply', 'Outward - Supply'),
        ('Outward - Export', 'Outward - Export'),
        ('Outward - Job Work', 'Outward - Job Work'),
        ('Inward - Supply', 'Inward - Supply')
    ], string="Reason for Transportation", default='Outward - Supply')

    def action_open_waybill_wizard(self):
        self.ensure_one()
        wizard = self.env['account.move.waybill.wizard'].create({
            'move_id': self.id,
            'ewaybill_no': self.x_ewaybill_no,
            'ewaybill_date': self.x_ewaybill_date,
            'transporter_name': self.x_transporter_name,
            'vehicle_no': self.x_vehicle_no,
            'transportation_address': self.x_transportation_address,
            'transport_doc_no': self.x_transport_doc_no,
            'transport_doc_date': self.x_transport_doc_date,
            'transaction_type': self.x_transaction_type,
            'reason_for_transport': self.x_reason_for_transport,
        })
        return {
            'name': 'Update Waybill Details',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move.waybill.wizard',
            'res_id': wizard.id,
            'target': 'new',
        }
