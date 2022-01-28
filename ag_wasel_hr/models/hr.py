from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta,date
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# HR Contract Changes
class HRContract(models.Model):
    _inherit = 'hr.contract'


    contract_type = fields.Selection([
        ('employee', 'Employee'),
        ('faculty', 'Faculty'),
        ('temperory', 'Temperory'),
    ], string='Type',required=True)
    qualification = fields.Selection([
        ('bachelor', 'Bachelor'),
        ('diploma', 'diploma'),
        ('scondery school', 'Scondery School'),
        ('below secondary', 'Below Secondary'),], string='Qualification')
    grade_id = fields.Many2one('grade.degree',string="Grade")
    years_of_experience = fields.Float('Years Of Experience')
    academic_title = fields.Selection([
        ('professor', 'Professor'),
        ('associate professor', 'Associate Professor'),
        ('assistant professor', 'Assistant Professor'),
        ('lecturer', 'Lecturer'),], string='Academic Title')
    academic_qualification = fields.Selection([
        ('PhD', 'PhD'),
        ('Master', 'Master'),
        ('Bachelor', 'Bachelor')], string='Academic Qualification')


# Grade Master
class Grades(models.Model):
    _name = 'grade.degree'

    name = fields.Char('Name')
    code = fields.Char('Code')
    level_id = fields.One2many('grade.level','grade_id',string="Levels")

class Levels(models.Model):
    _name = 'grade.level'

    grade_id = fields.Many2one('grade.degree',string="Grade")
    name = fields.Char('Name')
    code = fields.Integer('Code')
    low = fields.Float('Low')
    medium = fields.Float('Medium')
    high = fields.Float('High')


# HR Employee Changes
class HREmployee(models.Model):
    _inherit = 'hr.employee'

    employee_number = fields.Char('Employee Number',copy=False)
    childs_id = fields.One2many('emp.childs','employee_id',string="Childrens")
    second_job_position = fields.Many2one('hr.job',string="Second Job Position")
    qualification = fields.Selection([
        ('PhD', 'PhD'),
        ('Master', 'Master')], string='Academic Qualification')



    _sql_constraints = [
        ('employee_number_uniq', 'unique (employee_number)', 'The employee number must be unique!')
    ]

# Childrens Master
class Children(models.Model):
    _name = 'emp.childs'

    employee_id = fields.Many2one('hr.employee',string="Employees")
    name = fields.Char('Name')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),], string='Gender')
    birthday = fields.Date('Birthday')


# Special Allowance Screen
class HRSpecialAllowance(models.Model):
    _name = 'hr.special.allowance'
    _inherit = "mail.thread"

    name = fields.Char('Name',compute="get_name",store=True)
    employee_id = fields.Many2one('hr.employee',string='Employee',tracking=True)
    allowance_type = fields.Many2one('allowance.type',string="Allowance Type",tracking=True)
    amount = fields.Float('Amount')
    reference = fields.Char('Reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')], string='Status',default='draft',tracking=True)

    @api.depends('employee_id','allowance_type')
    def get_name(self):
        for rec in self:
            if rec.allowance_type and rec.employee_id:
                rec.name = "%s : %s"%(rec.allowance_type.name,rec.employee_id.name)
            elif rec.allowance_type and not rec.employee_id:
                rec.name = "%s "%(rec.allowance_type.name)
            elif not rec.allowance_type and rec.employee_id:
                rec.name = "%s "%(rec.employee_id.name)
            else:
                rec.name = ""

    def action_confirm(self):
        self.write({'state':'confirmed'})

    def action_approve(self):
        self.write({'state':'approved'})

class AllowanceType(models.Model):
    _name = 'allowance.type'

    name = fields.Char('Name')
    account_id = fields.Many2one('account.account',string='Account')


# HR Overtime Screen
class HROvertimes(models.Model):
    _name = 'hr.overtimes'
    _inherit = "mail.thread"

    name = fields.Char('Name',tracking=True)
    code = fields.Char('Code')
    date_from = fields.Date('Date From',tracking=True)
    date_to = fields.Date('Date To',tracking=True)
    department_id = fields.Many2one('hr.department',string='Department',tracking=True)
    line_ids = fields.One2many('hr.overtimes.line','overtime_id',string="Overtimes Lines")
    workday_hours_total = fields.Float('Total Worked Hours',compute="get_totals",store=True,tracking=True)
    offday_hours_total = fields.Float('Total Offday Hours',compute="get_totals",store=True,tracking=True)
    overtime_amount_total = fields.Float('Total Overtime',compute="get_totals",store=True,tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')], string='Status',default='draft',tracking=True)

    @api.model
    def create(self,vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('hr.overtimes.sequence')
        return super(HROvertimes,self).create(vals)

    @api.depends('line_ids')
    def get_totals(self):
        for rec in self:
            if rec.line_ids:
                rec.workday_hours_total = sum(rec.line_ids.mapped('worked_hours'))
                rec.offday_hours_total = sum(rec.line_ids.mapped('offday_hours'))
                rec.overtime_amount_total = sum(rec.line_ids.mapped('overtime_amount'))
            else:
                rec.workday_hours_total = 0.0
                rec.offday_hours_total = 0.0
                rec.overtime_amount_total = 0.0

    def action_submit(self):
        self.write({'state':'submitted'})
    
    def action_confirm(self):
        self.write({'state':'confirmed'})

    def action_approve(self):
        self.write({'state':'approved'})

class HROvertimesLine(models.Model):
    _name = 'hr.overtimes.line'

    overtime_id = fields.Many2one('hr.overtimes',string="Overtime")
    employee_id = fields.Many2one('hr.employee',string='Employee')
    worked_hours = fields.Float('Worked Hours')
    offday_hours = fields.Float('Offday Hours')
    wage = fields.Float('Wage')
    overtime_amount = fields.Float('Overtime Amount',compute="_get_overtime_amount",store=True)

    @api.depends('worked_hours','offday_hours','wage')
    def _get_overtime_amount(self):
        for rec in self:
            worked = (rec.worked_hours * 125 * rec.wage) / 100
            off = (rec.offday_hours * 150 * rec.wage) / 100
            rec.overtime_amount = worked + off


# HR Time-off  Changes
class HROvertimes(models.Model):
    _inherit = 'hr.leave'

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('suspended', 'Suspended')
        ], string='Status', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")
    request_date_to = fields.Date('Request End Date',tracking=True)

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date_state(self):
        if self.env.context.get('leave_skip_state_check'):
            return
        for holiday in self:
            if holiday.state in ['cancel', 'refuse', 'validate1']:
                raise ValidationError(_("This modification is not allowed in the current state."))

    def suspend_leave(self):
        self.write({'request_date_to':date.today(),'state':'suspended'})

