# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HrLeaveRequest(models.Model):
    _inherit = 'hr.leave'

    remaining_leaves = fields.Float(string='Remaining Legal Leaves', related='employee_id.remaining_leaves',
                                    help="Remaining legal leaves")
    overlapping_leaves = fields.Many2many('hr.leave', compute='get_overlapping_leaves', string='Overlapping Leaves',
                                          help="Overlapping leaves")
    #pending_tasks = fields.One2many('pending.task', 'leave_id', string='Pending Tasks', help="Pending tasks")
    holiday_managers = fields.Many2many('res.users', compute='get_hr_holiday_managers', help="Holiday managers")
    flight_ticket = fields.One2many('hr.flight.ticket', 'leave_id', string='Flight Ticket', help="Flight ticket")
    refuse_reason = fields.Text('Rejected Reason')
    # Commented for odoo 14 compatibility
    # double_validation = fields.Boolean(string='Apply Double Validation', related='holiday_status_id.double_validation')
    expense_account = fields.Many2one('account.account')
    leave_salary = fields.Selection([('0', 'Basic'), ('1', 'Gross')], string='Leave Salary')
    sick_leave_taken = fields.Integer('Sick Leaves Taken', compute='_sick_leaves_taken', store=True)
    current_date = fields.Date(string='Current Date')
    prev_half_paid_taken = fields.Integer('Previous Halfpaid Sick leaves Taken', compute='_sick_leaves_taken', store=True)

    sick_leave_requested = fields.Integer('Sick Leaves Requested', compute='_sick_leave_requested', store=True)
    #
    total_count = fields.Integer('Total Sick Count', compute='_total_sick_count', store=True)

    unpaid_count = fields.Integer('Unpaid Sick Leaves')  # ,compute='_total_pay')
    fullpaid_count = fields.Integer('Paid Sick Leaves')  # ,compute='_total_pay')

    halfpaid_count = fields.Integer('Half Paid Sick Leaves')  # ,compute='_total_pay'

    file = fields.Binary("Attachment", attachment=True)
    file_name = fields.Char("File Name")
    # column1="leave_id", column2="attachment_id", string="Attachments",required=True )

    annual_full_count = fields.Integer('Paid Annual Leaves')
    annual_unpaid_count = fields.Integer('Unpaid Annual Leaves')
    annual_leave_requested = fields.Float('Requested Annual Leaves', compute='_compute_annual_req_leave')



    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),  # YTI This state seems to be unused. To remove
        ('department_approve', 'Department Manager Approval'),
        ('confirm', 'HR Manager Approval'),
        ('refuse', 'Rejected'),
        ('validate1', 'Final Approval'),
        ('validate', 'Approved')
    ], string='Status', compute='_compute_state', default='department_approve',store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
             "\nThe status is 'To Approve', when time off request is confirmed by user." +
             "\nThe status is 'Refused', when time off request is refused by manager." +
             "\nThe status is 'Approved', when time off request is approved by manager.")

    @api.model_create_multi
    def create(self, vals_list):
        """ Override to avoid automatic logging of creation """
        if not self._context.get('leave_fast_create'):
            leave_types = self.env['hr.leave.type'].browse(
                [values.get('holiday_status_id') for values in vals_list if values.get('holiday_status_id')])
            mapped_validation_type = {leave_type.id: leave_type.leave_validation_type for leave_type in leave_types}

            for values in vals_list:
                employee_id = values.get('employee_id', False)
                leave_type_id = values.get('holiday_status_id')
                # Handle automatic department_id
                if not values.get('department_id'):
                    values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})

                # Handle no_validation
                if mapped_validation_type[leave_type_id] == 'no_validation':
                    values.update({'state': 'confirm'})

                if 'state' not in values:
                    # To mimic the behavior of compute_state that was always triggered, as the field was readonly
                    values['state'] = 'department_approve' if mapped_validation_type[leave_type_id] != 'no_validation' else 'draft'

                # Handle double validation
                if mapped_validation_type[leave_type_id] == 'both':
                    self._check_double_validation_rules(employee_id, values.get('state', False))

        holidays = super(HrLeaveRequest, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

        for holiday in holidays:
            if not self._context.get('leave_fast_create'):
                # Everything that is done here must be done using sudo because we might
                # have different create and write rights
                # eg : holidays_user can create a leave request with validation_type = 'manager' for someone else
                # but they can only write on it if they are leave_manager_id
                holiday_sudo = holiday.sudo()
                holiday_sudo.add_follower(employee_id)
                if holiday.validation_type == 'manager':
                    holiday_sudo.message_subscribe(partner_ids=holiday.employee_id.leave_manager_id.partner_id.ids)
                if holiday.validation_type == 'no_validation':
                    # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
                    holiday_sudo.action_validate()
                    holiday_sudo.message_subscribe(partner_ids=[holiday._get_responsible_for_approval().partner_id.id])
                    holiday_sudo.message_post(body=_("The time off has been automatically approved"),
                                              subtype_xmlid="mail.mt_comment")  # Message from OdooBot (sudo)
                elif not self._context.get('import_file'):
                    holiday_sudo.activity_update()
        return holidays

    def _check_double_validation_rules(self, employees, state):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.user_has_groups('hr_holidays.group_hr_holidays_responsible')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(_('You cannot first approve a time off for %s, because you are not his time off manager', employees[0].name))
        elif state == 'validate' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))

    @api.depends('holiday_status_id')
    def _compute_state(self):
        print('====new compute state')
        for holiday in self:
            if self.env.context.get('unlink') and holiday.state == 'draft':
                # Otherwise the record in draft with validation_type in (hr, manager, both) will be set to confirm
                # and a simple internal user will not be able to delete his own draft record
                holiday.state = 'draft'
            else:
                holiday.state = 'department_approve' if holiday.validation_type != 'no_validation' else 'draft'

    @api.depends('employee_id')
    def action_department_approval(self):
        for rec in self:
            if not rec.employee_id.leave_manager_id:
                raise ValidationError(
                    _("Please Assign a Department Manager or Time Off Approver to Employee.")
                )
            if rec.employee_id.leave_manager_id == self.env.user:
                rec.write({'state':'confirm'})
            else:
                raise ValidationError(
                    _("Only Department Managers Can Approve Leaves")
                )

    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'department_approve'})
        holidays = self.filtered(lambda leave: leave.validation_type == 'no_validation')
        if holidays:
            # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
            holidays.sudo().action_validate()
        self.activity_update()
        return True


    @api.depends('annual_leave_requested', 'holiday_status_id', 'employee_id', 'request_date_from', 'request_date_to')
    def _compute_annual_req_leave(self):
        self.annual_leave_requested = False
        for rec in self:

            ann_tot = 0
            leave_type = self.env['hr.leave.type'].search([('code', '=', 'ANNUAL')])
            # print('----leavtye---',leave_type.mapped(id))
            ann_new = False

            for type in leave_type:
                ann_new = type.name

            leave_type_name = ann_new
            print('---leave type---', leave_type_name)

            leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
                                                  ('request_date_from', '=', rec.request_date_from),
                                                  ('request_date_to', '=', rec.request_date_to),
                                                  ('holiday_status_id', 'in', leave_type_name),

                                                  ])

            for leave in leaves:
                # rt_date = datetime.strptime(str(leave.request_date_from), '%Y-%m-%d')
                # st_date = datetime.strptime(str(leave.request_date_to), '%Y-%m-%d')

                # delta = st_date - rt_date
                ann_tot = leave.number_of_days
            rec.annual_leave_requested = ann_tot
            print('----requested---', rec.annual_leave_requested)




    #

    # @api.depends('sick_leave_requested','unpaid_count','total_count','fullpaid_count','halfpaid_count')
    # def _total_pay(self):
    #     for rec in self:
    #         if rec.total_count < 16:
    #             rec.fullpaid_count = rec.sick_leave_requested
    #         elif rec.total_count > 15 and rec.total_count < 45:
    #             rec.halfpaid_count = rec.sick_leave_requested
    #         else:
    #             rec.unpaid_count = rec.sick_leave_requested

    @api.constrains("employee_id.joining_date", "request_date_from")
    def _check_join_dates(self):
        for leave in self:
            if leave.employee_id.joining_date and leave.request_date_from and leave.request_date_from < leave.employee_id.joining_date:
                raise ValidationError(
                    _("You cannot request for leave prior to joining date.")
                )



    @api.depends('sick_leave_taken', 'employee_id', 'holiday_status_id', 'request_date_from', 'prev_half_paid_taken')
    def _sick_leaves_taken(self):

        for rec in self:
            tot = 0
            half = 0

            # cdate = datetime.strptime(str(rec.current_date), '%Y-%m-%d')
            from_date = datetime.now().date().replace(month=1, day=1)
            leave_type = self.env['hr.leave.type'].search([('code', '=', 'SICK')])
            # print('----leavtye---',leave_type.mapped(id))
            new = False
            yr_dt_from = False
            yr_dt_to = False
            for type in leave_type:
                new = type.name
                if type.validity_start and type.validity_stop:
                    yr_dt_from = type.validity_start
                    yr_dt_to = type.validity_stop
            leave_type_name = new
            year_date_from = yr_dt_from
            year_date_to = yr_dt_to
            leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
                                                  ('request_date_from', '<', rec.request_date_from),
                                                  ('request_date_from', '>', from_date),
                                                  ('holiday_status_id', 'in', leave_type_name),
                                                  ('date_from', '<=', year_date_to),
                                                  ('date_to', '>=', year_date_from)
                                                  ])
            print('----sick_leaves---', leaves)

            for leave in leaves:
                tot += leave.number_of_days
                half += leave.halfpaid_count

            rec.sick_leave_taken = tot
            rec.prev_half_paid_taken = half
            rec.current_date = datetime.now().date().replace(month=1, day=1)

    @api.depends('holiday_status_id', 'employee_id', 'request_date_from', 'request_date_to', 'sick_leave_requested')
    def _sick_leave_requested(self):
        for rec in self:
            tot = 0
            leave_type = self.env['hr.leave.type'].search([('code', '=', 'SICK')])
            # print('----leavtye---',leave_type.mapped(id))
            new = False
            yr_dt_from = False
            yr_dt_to = False
            for type in leave_type:
                new = type.name
                if type.validity_start and type.validity_stop:
                    yr_dt_from = type.validity_start
                    yr_dt_to = type.validity_stop
            leave_type_name = new
            year_date_from = yr_dt_from
            year_date_to = yr_dt_to

            leaves = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
                                                  ('request_date_from', '=', rec.request_date_from),
                                                  ('request_date_to', '=', rec.request_date_to),
                                                  ('holiday_status_id', 'in', leave_type_name),
                                                  ('date_from', '<=', year_date_to),
                                                  ('date_to', '>=', year_date_from)
                                                  ])

            for leave in leaves:
                # rt_date = datetime.strptime(str(leave.request_date_from), '%Y-%m-%d')
                # st_date = datetime.strptime(str(leave.request_date_to), '%Y-%m-%d')

                # delta = st_date - rt_date
                tot = leave.number_of_days
            rec.sick_leave_requested = tot

    @api.depends('sick_leave_taken', 'sick_leave_requested')
    def _total_sick_count(self):
        for type in self:
            type.total_count = type.sick_leave_taken + type.sick_leave_requested


    # @api.depends('overlapping_leaves','date_from','date_to')
    def get_overlapping_leaves(self):

        if self.date_from and self.date_to:

            overlap_leaves = []
            from_date = self.date_from
            to_date = self.date_to
            r = (to_date + timedelta(days=1) - from_date).days
            leave_dates = [str(from_date + timedelta(days=i)) for i in range(r)]
            leaves = self.env['hr.leave'].search([('state', '=', 'validate'),
                                                  ('department_id', '=', self.department_id.id)])
            other_leaves = leaves - self
            for leave in other_leaves:
                frm_dte = leave.date_from
                to_dte = leave.date_to
                r = (to_dte + timedelta(days=1) - frm_dte).days
                leave_dtes = [str(frm_dte + timedelta(days=i)) for i in range(r)]
                if set(leave_dtes).intersection(set(leave_dates)):
                    overlap_leaves.append(leave.id)
            self.update({'overlapping_leaves': [(6, 0, overlap_leaves)]})
        else:
            self.overlapping_leaves = False

    def action_refuse(self):
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse leave requests.'))
        return super().action_refuse()

    def action_approve(self):

        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        # if self.holiday_status_id.code == 'SICK':
        #     if self.request_date_from and self.employee_id.contract_id.probation_period_end_date and self.request_date_from < self.employee_id.contract_id.probation_period_end_date:
        #         raise UserError(_('Employee is eligible for sick leaves only after completion of probation period.'))

        if self.total_count < 16:
            print('---enetered first condition--')
            self.fullpaid_count += self.sick_leave_requested
        elif self.total_count < 46:
            print('--enetered second cond---')
            if (self.total_count - self.sick_leave_requested) < 16:
                print('----second in cond---')
                self.fullpaid_count += 15 - (self.total_count - self.sick_leave_requested)
                self.halfpaid_count = self.sick_leave_requested - self.fullpaid_count
            else:
                print('--second else cond---')
                self.halfpaid_count = self.sick_leave_requested
        else:
            print('---entered third cond----')

            if self.sick_leave_taken:
                print('----sickkkkk---')

                current_half = 30 - self.prev_half_paid_taken
                print('---currenthalf----', current_half)
                # total_half = current_half + self.prev_half_paid_taken
                # print('---totalhal---',total_half)
                # if self.prev_half_paid_taken < 31:
                self.halfpaid_count = current_half
                self.unpaid_count = self.sick_leave_requested - self.halfpaid_count

                # else:
                #     self.halfpaid_count = 0
                #     self.unpaid_count = self.sick_leave_requested - self.halfpaid_count
#####################  ANNUAL ################################################
        if self.holiday_status_id.code == 'ANNUAL' and self.employee_id.earned_leaves_count < 0:
            raise UserError(_('Employee is having negative balance, Kindly mark remaining leaves as unpaid'))

        if self.annual_leave_requested and self.employee_id.earned_leaves_count and self.annual_leave_requested > self.employee_id.earned_leaves_count:

            self.annual_unpaid_count = self.annual_leave_requested - self.employee_id.earned_leaves_count
            print('----annualcount---', self.annual_unpaid_count)
        else:
            self.annual_full_count = self.annual_leave_requested
  ############ ANNUAL ##############################################################



        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))


            self.write({'state': 'validate1'})



    def action_draft(self):
        """ Reset all validation status to false when leave request
        set to draft stage"""
        # for user in self.leave_approvals:
        #     user.validation_status = False

        # self.sick_leave_taken = 0
        # self.prev_half_paid_taken = 0
        self.sick_leave_requested = 0

        self.total_count = 0
        self.unpaid_count = 0
        self.fullpaid_count = 0
        self.halfpaid_count = 0
        self.annual_unpaid_count = 0
        self.annual_full_count = 0
        self.annual_unpaid_count = 0
        self.annual_leave_requested = 0


        return super(HrLeaveRequest, self).action_draft()

    def book_ticket(self):
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can book flight tickets.'))
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_employee_id': self.employee_id.id,
            'default_leave_id': self.id,
        })

        return {
            'name': _('Book Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_vacation_mngmt.view_hr_book_flight_ticket_form').id,
            'res_model': 'hr.flight.ticket',
            'target': 'new',
            'context': ctx,
        }

    def get_hr_holiday_managers(self):
        self.holiday_managers = self.env.ref('hr_holidays.group_hr_holidays_manager').users

    def view_flight_ticket(self):
        return {
            'name': _('Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.flight.ticket',
            'target': 'current',
            'res_id': self.flight_ticket[0].id,
        }

    @api.model
    def send_leave_reminder(self):

        leave_request = self.env['hr.leave'].search([('state', '=', 'validate')])
        leave_reminder = self.env['ir.config_parameter'].sudo().get_param('leave_reminder')
        reminder_day_before = int(self.env['ir.config_parameter'].sudo().get_param('reminder_day_before'))
        mail_template = self.env.ref('hr_vacation_mngmt.email_template_hr_leave_reminder_mail')
        holiday_managers = self.env.ref('hr_holidays.group_hr_holidays_manager').users
        today = date.today()
        if leave_reminder:
            for request in leave_request:
                if request.date_from:
                    from_date = request.date_from

                    if reminder_day_before == 0:
                        prev_reminder_day = request.date_from
                    else:
                        prev_reminder_day = from_date - timedelta(days=reminder_day_before)
                    if prev_reminder_day.date() == today:
                        for manager in holiday_managers:
                            template = mail_template.sudo().with_context(
                                email_to=manager.email,
                            )
                            email_template_obj = self.env['mail.template'].browse(template.id)
                            values = email_template_obj.generate_email(request.id,
                                                                       ['subject', 'body_html', 'email_from',
                                                                        'email_to', 'partner_to', 'email_cc',
                                                                        'reply_to', 'scheduled_date'])
                            values['email_to'] = manager.email
                            msg_id = self.env['mail.mail'].create(values)
                            if msg_id:
                                msg_id._send()


# class PendingTask(models.Model):
#     _name = 'pending.task'
#
#     name = fields.Char(string='Task', required=True)
#     leave_id = fields.Many2one('hr.leave', string='Leave Request', help="Leave request")
#     dept_id = fields.Many2one('hr.department', string='Department', related='leave_id.department_id', help="Department")
#     project_id = fields.Many2one('project.project', string='Project', required=True, help="Project")
#     description = fields.Text(string='Description', help="Description")
#     assigned_to = fields.Many2one('hr.employee', string='Assigned to', help="Employee who is assigned to",
#                                   domain="[('department_id', '=', dept_id)]")
#     unavailable_employee = fields.Many2many('hr.employee', string='Unavailable Employees', help="unavailable employee",
#                                             compute='get_unavailable_employee')
#
#     def get_unavailable_employee(self):
#         unavail_emp = []
#         for leave in self.leave_id.overlapping_leaves:
#             unavail_emp.append(leave.employee_id.id)
#         self.update({'unavailable_employee': unavail_emp})


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    leave_reminder = fields.Boolean(string='Leave Reminder Email', help="Send leave remainder emails to hr managers")
    reminder_day_before = fields.Integer(string='Reminder Day Before')
    default_expense_account = fields.Many2one('account.account', string='Travel Expense Account',
                                              default_model='hr.leave')

    default_leave_salary = fields.Selection([('0', 'Basic'), ('1', 'Gross')], string='Leave Salary',
                                            default_model='hr.leave')

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        self.env['ir.config_parameter'].sudo().set_param('leave_reminder', self.leave_reminder)
        self.env['ir.config_parameter'].sudo().set_param('reminder_day_before', self.reminder_day_before)
        self.env['ir.config_parameter'].sudo().set_param('travel_expense_account', self.default_expense_account.id)

        self.env['ir.config_parameter'].sudo().set_param('default_leave_salary', self.default_leave_salary)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            leave_reminder=self.env['ir.config_parameter'].sudo().get_param('leave_reminder'),
            reminder_day_before=int(self.env['ir.config_parameter'].sudo().get_param('reminder_day_before')),
            default_expense_account=int(self.env['ir.config_parameter'].sudo().get_param('travel_expense_account', )),
            default_leave_salary=self.env['ir.config_parameter'].sudo().get_param('default_leave_salary'),
        )

        return res



class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    def _holiday_status_id_domains(self):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return [('valid', '=', True)]
        return [('valid', '=', True)]

    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Time Off Type", required=True,
        readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)],
                'validate': [('readonly', True)]},
        domain=_holiday_status_id_domains)

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    code = fields.Char('Code')
