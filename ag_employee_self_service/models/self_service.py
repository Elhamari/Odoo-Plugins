from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, fields, models, _
import re
import io
import base64
import sys
from PIL import Image
from odoo.exceptions import UserError,ValidationError


TAG_RE = re.compile(r'<[^>]+>')

class EmployeeSelfService(models.Model):
    _name = 'employee.self.service'
    _rec_name = 'seq_name'
    _description = "Employee Self Service"
    _inherit = 'mail.thread'


    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    seq_name = fields.Char(string='Serial No', required=True, copy=False, readonly=False, index=True, default=lambda self: _('New'))
    subject = fields.Char(string="Letter Title")
    employee = fields.Many2one('hr.employee', string='Employee',track_visibility='always',default=_get_employee_id)
   # emp_manager = fields.Char(string='Department Manager',compute='compute_emp_manager')
    #employee_id = fields.Char(string='Employee ID',related='employee_name.identification_id')
    date = fields.Date(string='Requested Date',default=datetime.today())
    employee_end_date = fields.Date(string='Last Working Date',track_visibility='always')
    old_employee_id = fields.Many2one('hr.employee', string="Employee Details")
    reason = fields.Text('Reason')
    #creator_manager = fields.Many2one('hr.employee',string="Department manager",copy=False,related='employee.parent_id')

    # file = fields.Binary("Attachment", attachment=True)
    # file_name = fields.Char("File Name")

    #user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange',
                             # track_sequence=2, default=lambda self: self.env.user)
    @api.model
    def _getUseraccess(self):
        selfservicce = self.env.user.has_group('ag_employee_self_service_user.group_self_service_user')
        hruser = self.env.user.has_group('hr.group_hr_user')
        hradmin = self.env.user.has_group('hr.group_hr_manager')
        if selfservicce and not hruser and not hradmin :
            return [('show_selfservice', '=', True)]
        else:
            return []
    #doc_type = fields.Many2one('template')
    document_type = fields.Many2one('template',domain=_getUseraccess)
    old_document_type_id = fields.Many2one('template')
    template = fields.Html(track_visibility='always')
    template_value = fields.Char(track_visibility='always')
    state = fields.Selection([
        ('new', 'New'),
        ('first', 'First Approval'),
        ('second', 'Second Approval'),
        ('third', 'Third Approval'),
        # ('reconfirm','HR Approval'),
        ('complete', 'Completed'),
        #('print', 'Print'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='new')

    image_stamp = fields.Image(string='Stamp')
    sign_man = fields.Many2one('hr.employee', string='HR Manager')


    @api.model
    def create(self, vals):

        if vals.get('seq_name', _('New')) == _('New'):
            vals['seq_name'] = self.env['ir.sequence'].next_by_code('self.service.sequence') or _('New')

        # vals['employee'] = self.env.uid
        # com = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        # for rec in com:
        #     vals['creator_manager'] = rec.parent_id.user_id.id
        res = super(EmployeeSelfService,self).create(vals)
        # self.on_change_employees()
        return res


    def send_approve(self):
        for letter in self:
            if letter.document_type.level1:
                self.write({'state': 'first'})
            else:
                self.write({'state':'complete'})

    def dept_approve(self):
        for letter in self:
            if letter.document_type.level1.id in self.env.user.groups_id.ids:
            # if self.env.user.has_group(letter.document_type.level1.name):
                # raise UserError('Mohon maaf tidak bisa ..')
                if letter.document_type.level2:
                    self.write({'state': 'second'})
                else:
                    self.write({'state':'complete'})
            else:
                raise UserError('You donot have access to approve this')


    def second_approve(self):
        for letter in self:
            if letter.document_type.level2.id in self.env.user.groups_id.ids:
            # if self.env.user.has_group(letter.document_type.level1.name):
                # raise UserError('Mohon maaf tidak bisa ..')
                if letter.document_type.level3:
                    self.write({'state': 'third'})
                else:
                    self.write({'state':'complete'})
            else:
                raise UserError('You donot have access to approve this')

    def third_approve(self):
        for letter in self:
            if letter.document_type.level3.id in self.env.user.groups_id.ids:
            # if self.env.user.has_group(letter.document_type.level1.name):
                # raise UserError('Mohon maaf tidak bisa ..')
                # if letter.document_type.level3:
                #     self.write({'state': 'third'})
                # else:
                self.write({'state':'complete'})
            else:
                raise UserError('You donot have access to approve this')




    def hr_approve(self):
        for letter in self:
            self.write({'state':'complete'})

    def print_event(self):
        return self.env.ref('ag_employee_self_service.print_pack_certificates').report_action(self)

    def print_preview(self):
        return self.env.ref('ag_employee_self_service.print_pack_certificates_new').report_action(self)
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined

    @api.onchange('document_type')
    def on_change_template(self):
        
        for rec in self:


            rec.subject = rec.document_type.title
            rec.sign_man = rec.document_type.sign_man.id

    # @api.onchange('employee_end_date')
    # def on_chnage_emp_enddate(self):
    #     if self.template:

    #         if 'end_date' in self.template:
    #             end_date = self.template.replace('end_date', str(self.employee_end_date))
    #             self.template = end_date

    @api.onchange('employee','document_type')
    def on_change_employees(self):
        if not self.template:
            self.template = self.document_type.template
            self.old_document_type_id = self.document_type.id
        if not self.old_document_type_id.id == self.document_type.id :
            self.template = self.document_type.template
            self.old_document_type_id = self.document_type.id
            self.old_employee_id = False
        if self.template:
            
            if self.old_employee_id:
                # if self.old_employee_id.id != self.employee.id:
                # raise UserError(self.old_employee_id)
                if self.old_employee_id.name in self.template:
                    employee_name = self.template.replace(self.old_employee_id.name, self.employee.name)
                    self.template = employee_name
                if str(self.old_employee_id.name_arabic) in self.template:
                    employee_name_ar = self.template.replace(str(self.old_employee_id.name_arabic), str(self.employee.name_arabic))
                    self.template = employee_name_ar

                if str(self.old_employee_id.passport_id) in self.template:
                    passport_no = self.template.replace(str(self.old_employee_id.passport_id), str(self.employee.passport_id))
                    self.template = passport_no

                if str(self.old_employee_id.mobile_phone) in self.template:
                    employee_mobile_phone = self.template.replace(str(self.old_employee_id.mobile_phone), str(self.employee.mobile_phone))
                    self.template = employee_mobile_phone
                if str(self.old_employee_id.country_id.name) in self.template:
                    nationality = self.template.replace(str(self.old_employee_id.country_id.name), str(self.employee.country_id.name))
                    self.template = nationality
                if str(self.old_employee_id.eid) in self.template:
                    emp_eid = self.template.replace(str(self.old_employee_id.eid), str(self.employee.eid))
                    self.template = emp_eid

                if str(self.old_employee_id.visa_no) in self.template:
                    emp_visa_no = self.template.replace(str(self.old_employee_id.visa_no), str(self.employee.visa_no))
                    self.template = emp_visa_no

                if str(self.old_employee_id.visa_expire) in self.template:
                    emp_visa_expire = self.template.replace(str(self.old_employee_id.visa_expire), str(self.employee.visa_expire))
                    self.template = emp_visa_expire
                if str(self.old_employee_id.permit_no) in self.template:
                    emp_permit_no = self.template.replace(str(self.old_employee_id.permit_no), str(self.employee.permit_no))
                    self.template = emp_permit_no
                if str(self.old_employee_id.job_id.name) in self.template:
                    designation_id = self.template.replace(str(self.old_employee_id.job_id.name), str(self.employee.job_id.name))
                    self.template = designation_id

                if str(self.old_employee_id.company_id.name) in self.template:
                    company_ids = self.template.replace(str(self.old_employee_id.company_id.name), str(self.employee.company_id.name))
                    self.template = company_ids



                if str(self.old_employee_id.joining_date) in self.template:
                    join_date = self.template.replace(str(self.old_employee_id.joining_date), str(self.employee.joining_date))
                    self.template = join_date
                if self.old_employee_id.work_email in self.template:
                    employee_email = self.template.replace(self.old_employee_id.work_email, self.employee.work_email)
                    self.template = employee_email
                if str(self.old_employee_id.contract_id.wage) in self.template:
                    net_salary = self.template.replace(str(self.old_employee_id.contract_id.wage), str(self.employee.contract_id.wage))
                    self.template = net_salary

                # if str(self.old_employee_id.contract_id.amount_in_word) in self.template:
                #     amount_in_word = self.template.replace(str(self.old_employee_id.contract_id.amount_in_word),
                #                                        str(self.employee.contract_id.amount_in_word))
                #     self.template = amount_in_word

                if self.old_employee_id.department_id.name in self.template:
                    employee_department = self.template.replace(self.old_employee_id.department_id.name, self.employee.department_id.name)
                    self.template = employee_department

                self.old_employee_id = self.employee.id


            else:
                self.old_employee_id = self.employee.id
                if 'employee_name' in self.template:
                    if self.employee.name:
                        print('---emplyee_nm--')
                        employee_name = self.template.replace('employee_name', self.employee.name)
                        self.template = employee_name
                    else:
                        employee_name = self.template.replace('employee_name','')
                        self.template = employee_name
                if 'name_ar' in self.template:
                    if self.employee.name_arabic:
                        print('---emplyee_nm--')
                        employee_name_ar = self.template.replace('name_ar', self.employee.name_arabic)
                        self.template = employee_name_ar
                    else:
                        employee_name_ar = self.template.replace('name_ar','')
                        self.template = employee_name_ar

                if 'designation_id' in self.template:
                    if self.employee.job_id.name:
                        designation_id = self.template.replace('designation_id', str(self.employee.job_id.name))
                        self.template = designation_id
                    else:
                        designation_id = self.template.replace('designation_id', '')
                        self.template = designation_id

                if 'passport_no' in self.template:
                    if self.employee.passport_id:
                        passport_no = self.template.replace('passport_no', self.employee.passport_id)
                        self.template = passport_no
                    else:
                        passport_no = self.template.replace('passport_no', '')
                        self.template = passport_no

                if 'employee_mobile_phone' in self.template:
                    if self.employee.mobile_phone:
                        employee_mobile_phone = self.template.replace('employee_mobile_phone', self.employee.mobile_phone)
                        self.template = employee_mobile_phone
                    else:
                        employee_mobile_phone = self.template.replace('employee_mobile_phone', '')
                        self.template = employee_mobile_phone

                if 'nationality' in self.template:
                    if self.employee.country_id.name:
                        nationality = self.template.replace('nationality', str(self.employee.country_id.name))
                        self.template = nationality
                    else:
                        nationality = self.template.replace('nationality', '')
                        self.template = nationality

                if 'emp_eid' in self.template:
                    if self.employee.eid:
                        emp_eid = self.template.replace('emp_eid', self.employee.eid)
                        self.template = emp_eid
                    else:
                        emp_eid = self.template.replace('emp_eid', '')
                        self.template = emp_eid

                if 'emp_visa_no' in self.template:
                    if self.employee.visa_no:
                        emp_visa_no = self.template.replace('emp_visa_no', self.employee.visa_no)
                        self.template = emp_visa_no
                    else:
                        emp_visa_no = self.template.replace('emp_visa_no', '')
                        self.template = emp_visa_no

                if 'emp_visa_expiry' in self.template:
                    if self.employee.visa_expire:
                        emp_visa_expiry = self.template.replace('emp_visa_expiry', str(self.employee.visa_expire))
                        self.template = emp_visa_expiry
                    else:
                        emp_visa_expiry = self.template.replace('emp_visa_expiry', '')
                        self.template = emp_visa_expiry

                if 'emp_permit_no' in self.template:
                    if self.employee.permit_no:
                        emp_permit_no = self.template.replace('emp_permit_no', self.employee.permit_no)
                        self.template = emp_permit_no
                    else:
                        emp_permit_no = self.template.replace('emp_permit_no', '')
                        self.template = emp_permit_no

                if 'net_salary' in self.template:
                    if self.employee.contract_id.wage:
                        net_salary = self.template.replace('net_salary', str(self.employee.contract_id.wage))
                        self.template = net_salary
                    else:
                        net_salary = self.template.replace('net_salary', '')
                        self.template = net_salary

                # if 'amount_in_word' in self.template:
                #     if self.employee.contract_id.amount_in_word:
                #         amount_in_word = self.template.replace('amount_in_word', str(self.employee.contract_id.amount_in_word))
                #         self.template = amount_in_word
                #     else:
                #         amount_in_word = self.template.replace('amount_in_word', '')
                #         self.template = amount_in_word

                if 'employee_email' in self.template:
                    if self.employee.work_email:
                        employee_email = self.template.replace('employee_email', self.employee.work_email)
                        self.template = employee_email
                    else:
                        employee_email = self.template.replace('employee_email', '')
                        self.template = employee_email
                if 'employee_department' in self.template:
                    if self.employee.department_id.name:
                        employee_department = self.template.replace('employee_department', self.employee.department_id.name)
                        self.template = employee_department
                    else:
                        employee_department = self.template.replace('employee_department', '')
                        self.template = employee_department
                if 'company_ids' in self.template:
                    if self.employee.company_id.name:
                        company_ids = self.template.replace('company_ids', self.employee.company_id.name)
                        self.template = company_ids
                    else:
                        company_ids = self.template.replace('company_ids', '')
                        self.template = company_ids
                if 'join_date' in self.template:
                    if self.employee.joining_date:
                        join_date = self.template.replace('join_date', str(self.employee.joining_date))
                        self.template = join_date
                    else:
                        join_date = self.template.replace('join_date', '')
                        self.template = join_date



            template = TAG_RE.sub('\n', self.template)
            self.template_value = template


    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        if force_confirmation_template or (self.state == 'draft'):
            template_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'ag_employee_self_service.default_confirmation_template'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data'].xmlid_to_res_id(
                    'ag_employee_self_service.email_template_letters', raise_if_not_found=False)
        if not template_id:
            template_id = self.env['ir.model.data'].xmlid_to_res_id(
                'ag_employee_self_service.email_template_letters', raise_if_not_found=False)

        return template_id


    def send_email(self):
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'employee.self.service',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class Template(models.Model):

    _name = 'template'
    _description = 'Template'
    _rec_name= 'template_name'

    template_name = fields.Char('Template Name')
    title = fields.Char('Title')

    template = fields.Html()
    image_stamp = fields.Image(string='Stamp')
    sign_man = fields.Many2one('hr.employee', string='Signatory')
    show_selfservice = fields.Boolean('Show to Self Service')
    level1 = fields.Many2one('res.groups', string='First Level Approval')
    level2 = fields.Many2one('res.groups', string='Second Level Approval')
    level3 = fields.Many2one('res.groups', string='Third Level Approval')

    @api.constrains('image_stamp')
    def check_insert_image_product(self):
        if self.image_stamp:
            file_image = base64.b64decode(self.image_stamp)
            stream = io.BytesIO(file_image)
            img = Image.open(stream)
            width, height = img.size
            if width > 167 or height > 167 and width < 167 or height < 167:
                raise ValidationError(
                    _("Please insert image with height or width of 167 (167 x 167) pixels"))
            image_size = sys.getsizeof(file_image) * 0.0009765625
            if image_size > 41.6 and image_size < 41.6 :
                raise ValidationError(_("Please insert image with size 41.6 KB.\nSize: %s" % (image_size)))


class Employee(models.Model):
    _inherit = 'hr.employee'

    name_arabic = fields.Char('Name in arabic')




