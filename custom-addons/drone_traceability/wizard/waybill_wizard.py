# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveWaybillWizard(models.TransientModel):
    _name = 'account.move.waybill.wizard'
    _description = 'Waybill Update Wizard'

    move_id = fields.Many2one('account.move', string="Invoice", required=True)
    ewaybill_no = fields.Char(string="e-Way Bill No")
    ewaybill_date = fields.Date(string="e-Way Bill Date")
    transporter_name = fields.Char(string="Transporter Name")
    vehicle_no = fields.Char(string="Vehicle / Trans Doc No")
    transportation_address = fields.Char(string="Transportation Address")
    transport_doc_no = fields.Char(string="Document No.")
    transport_doc_date = fields.Date(string="Document Date")
    transaction_type = fields.Selection([
        ('Regular', 'Regular'),
        ('Bill To - Ship To', 'Bill To - Ship To'),
        ('Bill From - Dispatch From', 'Bill From - Dispatch From'),
        ('Transit', 'Transit')
    ], string="Transaction Type", default='Regular')
    reason_for_transport = fields.Selection([
        ('Outward - Supply', 'Outward - Supply'),
        ('Outward - Export', 'Outward - Export'),
        ('Outward - Job Work', 'Outward - Job Work'),
        ('Inward - Supply', 'Inward - Supply')
    ], string="Reason for Transportation", default='Outward - Supply')

    def action_save_waybill(self):
        self.ensure_one()
        self.move_id.write({
            'x_ewaybill_no': self.ewaybill_no,
            'x_ewaybill_date': self.ewaybill_date,
            'x_transporter_name': self.transporter_name,
            'x_vehicle_no': self.vehicle_no,
            'x_transportation_address': self.transportation_address,
            'x_transport_doc_no': self.transport_doc_no,
            'x_transport_doc_date': self.transport_doc_date,
            'x_transaction_type': self.transaction_type,
            'x_reason_for_transport': self.reason_for_transport,
        })
