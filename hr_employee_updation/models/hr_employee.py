# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    # Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY # Technologies (<https://www.#.com>).
#    Author: Jesni Banu (<https://www.#.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta
from odoo import models, fields, _, api

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    member_name = fields.Char(string='Name')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)


class HrReligion(models.Model):
    _name = "hr.religion"
    _description = "Employee Religion"

    name = fields.Char(string="Name", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'



    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    # personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True,
    #               help="Personal mobile number of the employee")
    joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date", store=True)#,compute='compute_joining',
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    departure_reason = fields.Selection([
        ('fired', 'Terminated'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired')
    ], string="Archived Reason", groups="hr.group_hr_user", copy=False, tracking=True)
    departure_date = fields.Date(string="Archived Date", groups="hr.group_hr_user", copy=False, tracking=True)

    identification_id = fields.Char(string='Employee No', groups="hr.group_hr_user", tracking=True, store=True,
                                    compute='_compute_employee_code')
    sequence = fields.Char('Sequence', readonly=True, copy=False)
    # asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    eid = fields.Char('Emirates ID', tracking=True)
    yrs_of_exp = fields.Integer('Years Of Experience', tracking=True)
    religion = fields.Many2one('hr.religion', string='Religion', tracking=True)

    job_title = fields.Char("Job Title", compute="_compute_job_title", store=True, readonly=False, tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', tracking=True,
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    work_phone = fields.Char('Work Phone', compute="_compute_phones", store=True, readonly=False, tracking=True)
    mobile_phone = fields.Char('Work Mobile', tracking=True)
    work_email = fields.Char('Work Email', tracking=True)
    parent_id = fields.Many2one('hr.employee', 'Manager', compute="_compute_parent_id", store=True, readonly=False,
                                tracking=True)
    address_id = fields.Many2one('res.partner', 'Work Address', compute="_compute_address_id", store=True,
                                 readonly=False,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 tracking=True)
    work_location = fields.Char('Work Location', tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar',
                                           domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                           tracking=True)
    tz = fields.Selection(string='Timezone', readonly=False,
                          help="This field is used in order to define in which timezone the resources will work.",
                          tracking=True)
    user_id = fields.Many2one('res.users', 'User', related='resource_id.user_id', store=True, readonly=False,
                              tracking=True)
    job_id = fields.Many2one('hr.job', 'Job Position',
                             domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                             tracking=True)

    #asset_id = fields.One2many('hr.employee.asset', 'employee', string='Employee Asset')

    def _get_date_start_work(self):
        join_dates = self.joining_date
        join_time = datetime.min.time()
        join_date = datetime.combine(join_dates, join_time)
        return join_date

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('employee.seq') or '/'
        vals['sequence'] = seq

        return super(HrEmployee, self).create(vals)

    @api.depends('identification_id', 'sequence', )
    def _compute_employee_code(self):
        for rec in self:
            if rec.sequence:
                rec.identification_id = rec.sequence
            else:
                rec.identification_id = False


    # @api.depends('contract_id')
    # def compute_joining(self):
    #     if self.contract_id:
    #         date = min(self.contract_id.mapped('date_start'))
    #         self.joining_date = date
    #     else:
    #         self.joining_date = False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        lines_info = []
        spouse_name = self.spouse_complete_name
        date = self.spouse_birthdate
        if spouse_name and date:
            lines_info.append((0, 0, {
                'member_name': spouse_name,
                'relation_id': relation.id,
                'birth_date': date,
            })
                              )
            self.fam_ids = [(6, 0, 0)] + lines_info


class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'

    name = fields.Char(string="Relationship", help="Relationship with thw employee")



class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    departure_reason = fields.Selection([
        ('fired', 'Terminated'),
        ('resigned', 'Resigned'),
        ('retired', 'Retired')
    ], string="Departure Reason", default="fired")