from odoo import api, fields, models, tools,_
from odoo.exceptions import except_orm, ValidationError ,UserError
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta , date
import math
import time
from num2words import num2words
from odoo.exceptions import Warning
from odoo.tools import float_utils, float_compare ,pycompat ,email_re, email_split, email_escape_char, float_is_zero, date_utils

from odoo.tools.misc import format_date

class HRpayrolltran(models.Model):
    _name = 'hr.payroll.transactions'

    state = fields.Selection(string='Status', selection=[
        ('draft', 'New'),
        ('confirm', 'Waiting Approval'),
        ('accepted', 'Approved'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancelled', 'Refused')],
                             copy=False, index=True, readonly=True, default="draft")
    date_from = fields.Date('Date')
    date_to = fields.Date('To')
    date = fields.Date('Date')
    name = fields.Char('Description')
    payroll_tran_line = fields.One2many('hr.payroll.transactions.line', 'payroll_tran_id',
                                        string='Payroll Transactions')

    #
    def unlink(self):
        for line in self:
            if line.state in ['paid', 'done']:
                raise UserError(_('Cannot delete a transaction which is in state \'%s\'.') % (line.state,))
        return super(HRpayrolltran, self).unlink()

    #
    def loans_confirm(self):
        for rec in self:
            for l in rec.payroll_tran_line:
                l.state = 'accepted'
        return self.write({'state': 'done'})

    #
    def loans_accept(self):
        return self.write({'state': 'done'})

    #
    def loans_refuse(self):
        return self.write({'state': 'cancelled'})

    #
    def loans_set_draft(self):
        return self.write({'state': 'draft'})


class HRpayrolltranLine(models.Model):
    _name = 'hr.payroll.transactions.line'

    payroll_tran_id = fields.Many2one('hr.payroll.transactions')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    timesheet_cost = fields.Float('Timesheet Cost')
    number_of_hours = fields.Float('No of Hours')
    tran_note = fields.Char('Transaction')
    allowance = fields.Float('Allowance')
    deduction = fields.Float('Deduction')
    payroll_item = fields.Many2one('hr.salary.rule', string="Payroll Item", required=True)
    analytic_account = fields.Many2one('account.analytic.account', string="Analytic Account")
    state = fields.Selection(string='Status', selection=[
        ('draft', 'New'),
        ('cancelled', 'Refused'),
        ('confirm', 'Waiting Approval'),
        ('accepted', 'Approved'),
        ('done', 'Waiting Payment'),
        ('paid', 'Paid')], readonly=True)

    @api.onchange('number_of_hours')
    def _get_amount(self):
        for rec in self:
            rec.timesheet_cost = rec.employee_id.timesheet_cost

            rec.allowance = rec.number_of_hours * rec.timesheet_cost


class HrPayslipcus(models.Model):
    _inherit = 'hr.payslip'

    hr_variance_line_id = fields.One2many('hr.variance.line', 'payslip_id', string="Variance")

    #
    def unlink(self):
        for rec in self:
            if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
                raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))
            if rec.state == 'draft':
                if rec.hr_variance_line_id:
                    raise UserError(_('Please delete the variance line and reset to draft the payroll transactions in order to delete the payslip!'))
        return super(HrPayslipcus, self).unlink()


class HrVarianceLine(models.Model):
    _name = 'hr.variance.line'

    payslip_id = fields.Many2one('hr.payslip')
    tran_id = fields.Many2one('hr.payroll.transactions', string="Transaction")
    rule_id = fields.Many2one('hr.salary.rule', string="Rule")
    date_value = fields.Date('Date')
    tran_note = fields.Char('Transaction Note')
    amount = fields.Float('Amount')


class HrPayslipEmployeescus(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    #
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')

        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        # add payroll transaction

        datas = {}
        obj = self.env['hr.payroll.transactions'].search([('date_from', '>=', from_date), ('date_from', '<=', to_date)])
        # add payroll transaction
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            # add payroll transaction
            invoice_line = []
            for l in obj:
                if l.state == 'done':
                    for k in l.payroll_tran_line:
                        if k.state != 'paid':
                            if k.employee_id.id == employee.id:
                                datas = {
                                    'tran_id': l.id,
                                    'rule_id': k.payroll_item.id,
                                    'date_value': l.date_from,
                                    'tran_note': k.tran_note,
                                    'amount': k.allowance,
                                }
                                invoice_line.append((0, 0, datas))
                                k.state = 'paid'
                            else:
                                continue
                        else:
                            continue
                else:
                    continue

            # add payroll transaction
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'hr_variance_line_id': invoice_line,
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        # for l in obj:
        #         l.state = 'paid'
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}

    # view of payroll transaction Report
class HrSalaryRulecus(models.Model):
    _inherit = 'hr.salary.rule'

    od_payroll_item = fields.Boolean('Payroll Item', default=False)

class HrPayrollTranSheetView(models.Model):
    _name = 'hr.payroll.tran.sheet.view'
    _description = "Payroll transaction Report"
    _auto = False

    amount = fields.Float('Amount')
    date = fields.Date('Date')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    payroll_item = fields.Many2one('hr.salary.rule', string="Payroll Item")
    tran = fields.Char('Transaction')
    description = fields.Char('Description')

    @api.model
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

    def _select(self):
        select_str = """
                SELECT 
                    min(ptl.id) as id,
                    ptl.employee_id,
                    ptl.payroll_item,
                    ptl.tran_note as tran,
                    ptl.allowance as amount,
                    pt.date_from as date,
                    pt.name as description

        """
        return select_str

    def _from(self):
        from_str = """
            hr_payroll_transactions_line ptl
                LEFT JOIN hr_payroll_transactions pt on (ptl.payroll_tran_id = pt.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                ptl.employee_id,
                ptl.payroll_item,
                ptl.tran_note,
                ptl.allowance,
                pt.date_from,
                pt.name
        """
        return group_by_str

    # view of payroll transaction Report
