# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    gantt_workcenter_id = fields.Many2one(
        'mrp.workcenter', 
        string='Target Machine',
        help='Select a machine here to automatically generate a Work Order when confirmed.'
    )
    gantt_duration_expected = fields.Float(
        string='Expected Duration (Hours)',
        default=1.0,
        help='How many hours will this job take on the selected machine?'
    )

    def action_confirm(self):
        # Call the original method to transition the MO to confirmed
        res = super(MrpProduction, self).action_confirm()

        for mo in self:
            # If the user selected a target machine and there are no existing work orders 
            # (which means there was no BOM/Routing with operations defined)
            if mo.gantt_workcenter_id and not mo.workorder_ids:
                # Create a simple work order for the MO on the selected machine
                duration_minutes = mo.gantt_duration_expected * 60.0
                
                self.env['mrp.workorder'].create({
                    'name': 'Gantt Job - ' + mo.product_id.name,
                    'production_id': mo.id,
                    'workcenter_id': mo.gantt_workcenter_id.id,
                    'product_uom_id': mo.product_uom_id.id,
                    'duration_expected': duration_minutes,
                    'state': 'pending',
                })
        
        return res
