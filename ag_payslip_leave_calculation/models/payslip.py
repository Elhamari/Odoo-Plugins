
from odoo import api, fields, models, tools,_
from odoo.exceptions import except_orm, ValidationError ,UserError
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date ,time
import math
from num2words import num2words
from odoo.exceptions import Warning
from pytz import timezone

from odoo.tools import float_utils, float_compare ,pycompat ,email_re, email_split, email_escape_char, float_is_zero, date_utils

from odoo.tools.misc import format_date



class HrPayslipcus(models.Model):
    _inherit = 'hr.payslip'

    hr_variance_line_id = fields.One2many('hr.variance.line','payslip_id',string="Variance")
    days = fields.Integer('Days',compute='_compute_days')
    # current_leave_taken = fields.Integer('Current Sick')#,compute='_get_sick_leaves')
    # previous_leave_taken = fields.Integer('Preveious Sick')
    # total_leaves_taken = fields.Integer('Total Sick')
    previous_half_leave_count = fields.Integer(string='Total half pay Leaves',compute='_total_half',store=True)
    tot_annual_leave_bal = fields.Float(string='Total Balance Leaves',compute='_bal_leaves',store=True)
    remarks = fields.Text(string="Remarks", help='Remarks')


    @api.depends('previous_half_leave_count','employee_id','date_from')
    def _total_half(self):

        for rec in self:
            tot = 0
            new = False
            from_date = datetime.now().date().replace(month=1, day=1)
            leave_type = self.env['hr.leave.type'].search([('code','=','SICK')])
            #print('----leavtye---',leave_type.mapped(id))
            for type in leave_type:
                new = type.name
            leave_type_name = new
            #new = leave_type.mapped(id)
            #print('---leave---',new)
            leaves = self.env['hr.leave'].search(['&',('employee_id','=',rec.employee_id.id),
                                                      ('request_date_from','<',rec.date_from),
                                                      ('request_date_from','>',from_date),
                                                      ('holiday_status_id','in',leave_type_name)
                                                      ])
            print('----leavessss----',leaves)
            for leave in leaves:
                tot += leave.halfpaid_count

            rec.previous_half_leave_count = tot

    @api.depends('tot_annual_leave_bal','employee_id','date_from','date_to')
    def _bal_leaves(self):
        for rec in self:
            ann_tot = 0
            annual_new = False
            from_date = datetime.now().date().replace(month=1, day=1)
            leave_type = self.env['hr.leave.type'].search([('code','=','ANNUAL')])
            #print('----leavtye---',leave_type.mapped(id))
            for type in leave_type:
                annual_new = type.name
            leave_type_name = annual_new
            #new = leave_type.mapped(id)
            #print('---leave---',new)
            leaves = self.env['hr.leave'].search(['&',('employee_id','=',rec.employee_id.id),
                                                      ('request_date_from','>=',rec.date_from),
                                                      ('request_date_to', '<=', rec.date_to),
                                                      ('holiday_status_id','in',leave_type_name)
                                                      ])
            print('----annualleavessss----',leaves)
            for leave in leaves:
                ann_tot += leave.annual_unpaid_count
                print('---ann_tot---',ann_tot)

            rec.tot_annual_leave_bal = ann_tot


    @api.depends('date_from','date_to')
    def _compute_days(self):

        start = self.date_from
        end = self.date_to

        delta = end - start
        dayss = delta.days + 1
        self.days = dayss

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        start_date_yr = datetime.now().date().replace(month=1, day=1)

        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            if contract.employee_id.joining_date:
                start_date_all_year = contract.employee_id.joining_date
            else:
                raise ValidationError(_('Make sure to enter joining date of all employees'))

                #contract.date_start
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
            starting_day_of_current_year = datetime.combine(fields.Date.from_string(start_date_yr),time.min)
            starting_day_of_all_year = datetime.combine(fields.Date.from_string(start_date_all_year),time.min)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,calendar=contract.employee_id.resource_calendar_id)
            day_leave_previous = contract.employee_id.list_leaves(starting_day_of_current_year, day_from,calendar=contract.employee_id.resource_calendar_id)
            day_leave_previous_year = contract.employee_id.list_leaves(starting_day_of_all_year, day_from,calendar=contract.employee_id.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave[:1].holiday_id

                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'previous_leave_count':0.0,
                    'total_leave_count':0.0,
                    'total_leave_year_count':0.0,
                    'contract_id': contract.id,
                })

                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours
                   # current_leave_struct['previous_leave_count'] += hours / work_hours
                    current_leave_struct['total_leave_count'] += hours / work_hours
                    current_leave_struct['total_leave_year_count'] += hours / work_hours

            for day, hours, leave in day_leave_previous:
                holiday = leave[:1].holiday_id
                if holiday.holiday_status_id in leaves:


                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        leaves[holiday.holiday_status_id]['previous_leave_count'] += hours / work_hours
                        leaves[holiday.holiday_status_id]['total_leave_count'] += hours / work_hours

            for day, hours, leave in day_leave_previous_year:
                holiday = leave[:1].holiday_id
                if holiday.holiday_status_id in leaves:

                    work_hours = calendar.get_work_hours_count(
                        tz.localize(datetime.combine(day, time.min)),
                        tz.localize(datetime.combine(day, time.max)),
                        compute_leaves=False,
                    )
                    if work_hours:
                        leaves[holiday.holiday_status_id]['total_leave_year_count'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    previous_leave_count = fields.Integer(string='Previous Month leaves')
    total_leave_count = fields.Integer(string='Total Current leaves')
    total_leave_year_count = fields.Integer(string='Total Year Leaves')