# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class ChangeDate(models.TransientModel):
    _name = 'change.date'
    _description = 'Change Date'

    date = fields.Date('New Date To',required=True)

    def action_change_date_apply(self):
        leave = self.env['hr.leave'].browse(self.env.context.get('active_ids'))
        if leave.request_date_to >= self.date:
            raise UserError('The new date should be bigger than the old one')
        else:
            leave.write({'request_date_to':self.date})
            
            
