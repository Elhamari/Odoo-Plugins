# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class RefuseReason(models.TransientModel):
    _name = 'refuse.reason.settle'
    _description = 'Get Lost Reason'

    refuse_reason = fields.Text('Reason of Refuse(Rejection)', required=True)

    def action_lost_reason_sett_leave_apply(self):
        # raise UserError(self.env.context.get('active_model'))
        if self.env.context.get('active_model') == 'final.settlement':
            leaves = self.env['final.settlement'].browse(self.env.context.get('active_ids'))
            leaves.write({'refuse_reason': self.refuse_reason})
            leaves.action_reject()


