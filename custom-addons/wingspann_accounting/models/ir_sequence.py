# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_prefix_variables(self):
        res = super(IrSequence, self)._get_prefix_variables()
        
        # Get the date context used by the sequence, defaulting to today
        seq_date = self.env.context.get('ir_sequence_date', fields.Date.today())
        if isinstance(seq_date, str):
            seq_date = fields.Date.from_string(seq_date)
            
        year = seq_date.year
        # Fiscal Year calculation (April 1 to March 31)
        if seq_date.month < 4:
            fy = f"{year - 1}-{str(year)[-2:]}"
        else:
            fy = f"{year}-{str(year + 1)[-2:]}"
            
        res['fy'] = fy
        return res
