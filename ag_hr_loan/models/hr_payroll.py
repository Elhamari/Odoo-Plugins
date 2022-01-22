# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = employee._get_contracts(date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0].id)

        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self._get_worked_day_lines()
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        if contracts:
            input_line_ids = self.get_inputs(contracts, date_from, date_to)
            input_lines = self.input_line_ids.browse([])
            
            for inp in input_line_ids:
                self.write({'input_line_ids': [(0, 0, inp)]})
        return



    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        loan_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LO')])
        advance_input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'SAR')])
        result = []
        contract_obj = self.env['hr.contract']
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
        adv_salary = self.env['salary.advance'].search([('employee_id', '=', self.employee_id.id)])
        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    result.append({'code': 'LO', 'amount': loan_line.amount, 'input_type_id':loan_input_type.id, 'loan_line_id':loan_line.id})
        for adv_obj in adv_salary:
            current_date = date_from.month
            date = adv_obj.date
            existing_date = date.month
            if current_date == existing_date:
                state = adv_obj.state
                amount = adv_obj.advance
                if state == 'approve' and amount != 0:
                    result.append({'code': 'LO', 'amount': amount, 'input_type_id':advance_input_type.id})
        return result

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
                line.loan_line_id.action_paid_amount()
        return super(HrPayslip, self).action_payslip_done()
