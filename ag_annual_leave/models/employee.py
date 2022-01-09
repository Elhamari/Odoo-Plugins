# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import tools



class HrEmployee(models.Model):
    _inherit = "hr.employee"

    earned_leaves_count = fields.Float('Annual Balance',compute='_earned_leaves_count')





    @api.depends()
    def _earned_leaves_count(self):
        print('---earned----')

        # leave_type = self.env['hr.leave.type'].search([
        #     ('code', 'ilike', 'ANNUAL'),
        # ])
        leaves = self.env['hr.leave.report'].read_group([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id', '=', 1),
            ('state', '=', 'validate')
        ], fields=['number_of_days', 'employee_id'], groupby=['employee_id'])
        print('=====leaves=====', leaves)
        mapping = dict([(leave['employee_id'][0], leave['number_of_days']) for leave in leaves])
        print('=======mappping=====', mapping)

        for employee in self:
            employee.earned_leaves_count = mapping.get(employee.id)
        # for employee in self:
        #     employee.earned_leaves_count = 0
        #     if leaves:
        #         employee.earned_leaves_count = leaves[0].get('employee_id_count')
        #         print('----employee earned leave count---', employee.earned_leaves_count)

    def action_view_earned_leaves(self):
        for rec in self:
            leave_type = self.env['hr.leave.type'].search([('code', 'ilike', 'ANNUAL')])
            holidays_id = self.env['hr.leave.report'].search([
                ('holiday_status_id', 'in', leave_type.ids),
                ('employee_id', '=', rec.id),
                ('state','=','validate')
            ])
            action = self.env.ref('ag_annual_leave.action_hr_employee_holiday_request')
            result = action.read()[0]
            result['domain'] = [('id', 'in', holidays_id.ids)]
        return result