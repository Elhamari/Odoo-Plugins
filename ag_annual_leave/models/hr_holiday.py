# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from datetime import datetime, time

from odoo.addons.resource.models.resource import HOURS_PER_DAY



class HrHolidays(models.Model):
    _inherit = "hr.leave.allocation"

    state = fields.Selection(
        track_visibility=None
    )
    annual_cron_date = fields.Date(
        string="Annual Date"
    )



    def name_get(self):
        res = []

        for leave in self:
            if leave.annual_cron_date:
                current_date = fields.Date.from_string(leave.annual_cron_date)
            else:
                current_date = fields.Date.from_string(leave.create_date)
            if current_date:
                current_month = current_date.strftime("%B")
                current_year = current_date.year

                if leave.holiday_status_id.code == 'ANNUAL':
                    #                 name = leave.holiday_status_id.name + ' Allocation - '+ leave.employee_id.name + ' - ' + current_month + ' ' + str(current_year)
                    name = leave.holiday_status_id.name + ' Allocation - ' + current_month + ' ' + str(current_year)
                    res.append((leave.id, name))
                else:
                    res.append((leave.id, _("%s on %s : %.2f day(s)") % (
                    leave.employee_id.name or leave.category_id.name, leave.holiday_status_id.name,
                    leave.number_of_days)))
        return res

    @api.model
    def _create_allocation_request_by_cron(self, employees, leave_type, leave_number):
        current_date = fields.Date.from_string(fields.Date.today())

        current_month = current_date.strftime("%B")
        current_year = current_date.year



        last_day = current_date + relativedelta(day=1, months=+1, days=-1)
        date_to = last_day.strftime("%Y-%m-%d")
        first_day = current_date + relativedelta(day=1)
        date_from = first_day.strftime("%Y-%m-%d")

        for emp in employees.filtered(lambda e: e.contract_id):
            print('---emp----',emp)
            print('---entered for loop---')
            contracts = self.env['hr.contract'].browse()

            worked_days_line_ids = self.env['hr.payslip'].get_worked_day_lines(contracts, date_from, date_to)
            print('----worked_dys_line----',worked_days_line_ids)
            was_on_full_month_leave = False
            for line in worked_days_line_ids:
                if line['code'] == 'WORK100':
                    if line['number_of_days'] == 0.0:
                        was_on_full_month_leave = True
                        break

            if not was_on_full_month_leave:
                print('----entered if cond---')
                name = leave_type.name  + ' Allocation - ' + emp.name + ' - ' + current_month + ' ' + str(current_year)
                vals = {'name': name,
                        'employee_id': emp.id,
                        'number_of_days': leave_number,
                        'department_id': emp.department_id.id,
                        'holiday_status_id': leave_type.id,
                        'holiday_type': 'employee',
                        'allocation_type': 'accrual',
                        'annual_cron_date': fields.Date.today(),
                        }

                print('-----leave values-----',vals)
                holiday = self.env['hr.leave.allocation'].create(vals)
                holiday.action_approve()
                if holiday.state == 'validate1':
                    holiday.action_validate()

    @api.model
    def cron_legal_leave_allocation_request(self):

        employees = self.env['hr.employee'].search([])
        print('-------employeee list----',employees)

        leave_type = self.env['hr.leave.type'].search([('code', 'ilike', 'ANNUAL')])
        leave_number = 2.5
        self._create_allocation_request_by_cron(employees, leave_type, leave_number)

