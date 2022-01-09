# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Time Off Status",
                           selection=[
                               ('draft', 'New'),
                               ('confirm', 'Waiting Approval'),
                               ('department_approve', 'Department Manager Approval'),
                               ('refuse', 'Refused'),
                               ('validate1', 'Waiting Second Approval'),
                               ('validate', 'Approved'),
                               ('cancel', 'Cancelled')
                           ])