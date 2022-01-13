from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, fields, models, _


class AdmissionCustom(models.Model):
    _inherit = 'op.admission'

    application_num = fields.Char('Appliction Number')
    nationality = fields.Many2one('res.country',string="Nationality")
    place_of_birth = fields.Many2one('res.country',string="place of birth")
    maturity_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widow', 'Widow'),
    ], string='Maturity Status')
    passport_number = fields.Char('Passport Number')
    passport_country_issue = fields.Many2one('res.country',string="Country Of Issued")
    passport_issued_date = fields.Date('Issued Date')
    passport_end_date = fields.Date('End Date')
    eid_number = fields.Char('EID Number')
    uid = fields.Char('UID')
    eid_end_date = fields.Date('End Date')
    residency_number = fields.Char('Residency Number')
    residency_state = fields.Selection([
        ('Abu Dhabi', 'Abu Dhabi'),
        ('Dubai', 'Dubai'),
        ('Sharjah', 'Sharjah'),
        ('Ajman', 'Ajman'),
        ('Umm Al-Quwain', 'Umm Al-Quwain'),
        ('Fujairah', 'Fujairah'),
        ('Ras Al Khaimah', 'Ras Al Khaimah'),
    ], string='Issue State')
    residency_issued_date = fields.Date('Issued Date')
    residency_end_date = fields.Date('End Date')
    # secondray school page details
    score = fields.Float('Score')
    certificate_type = fields.Many2one('certificate.type',string="Certificate Type")
    school_name = fields.Char('School Name')
    school_system = fields.Selection([
        ('UAE', 'UAE'),
        ('GULF country', 'GULF Country'),
        ('Arabian Country', 'Arabian Country'),
        ('Islamic Country', 'Islamic Country'),
        ('Other', 'Other'),
    ], string='Issue State')
    institute_type = fields.Many2one('institute.type',string="Institute Type")
    certificate_origin = fields.Char('Certificate Origin')
    sec_issued_date = fields.Date('Issue Date')
    sec_state = fields.Selection([
        ('Abu Dhabi', 'Abu Dhabi'),
        ('Dubai', 'Dubai'),
        ('Sharjah', 'Sharjah'),
        ('Ajman', 'Ajman'),
        ('Umm Al-Quwain', 'Umm Al-Quwain'),
        ('Fujairah', 'Fujairah'),
        ('Ras Al Khaimah', 'Ras Al Khaimah'),
    ], string='State')
    #parent details
    parent_ids = fields.One2many('parent.list','admission_id',string="Parents")
    
    # documents details
    personal_photo_bol = fields.Boolean('Personal Photo')
    personal_photo = fields.Binary('Personal Photo')
    cert_of_good_conduct_bol = fields.Boolean('Cert. Of Good Conduct')
    cert_of_good_conduct = fields.Binary('Cert. Of Good Conduct')
    medical_check_bol = fields.Boolean('Cert. Of Medical Check')
    medical_check = fields.Binary('Cert. Of Medical Check')
    passport_photo_bol = fields.Boolean('Passport')
    passport_photo = fields.Binary('Passport')
    birthday_cert_bol = fields.Boolean('Birthday Cert.')
    birthday_cert = fields.Binary('Birthday Cert.')
    pledge_bol = fields.Boolean('Acknowledgemt And Pledge')
    pledge = fields.Binary('Acknowledgemt And Pledge')
    # work details
    sector_type = fields.Many2one('sector.type',string="Sector Type")
    job_name = fields.Char('Job Name')
    employer_type = fields.Many2one('employer.type',string="Employer Type")
    job_country = fields.Many2one('res.country',string="Country")
    job_tel = fields.Char('Tel')
    job_email = fields.Char('Email')
    job_fax = fields.Char('Fax')
    job_notes = fields.Text('Notes')
    # special cases details
    case_name = fields.Char('Name')
    case_type = fields.Many2one('case.type',string="Case Type")
    # attitude test details
    attitude_line = fields.One2many('attitude.test','admission_id',string="Attitude Test")
    multi_address = fields.One2many('multi.address','admission_id',string="Addresses")





    @api.model
    def create(self,vals):
        vals['application_num'] = self.env['ir.sequence'].next_by_code('op.admission.application.sequence')
        res = super(AdmissionCustom,self).create(vals)

        return res

class Attitude(models.Model):
    _name = 'attitude.test'

    admission_id = fields.Many2one('op.admission',string="Admission Rel")
    date = fields.Date('Date')
    score = fields.Float('Score')
    test_type = fields.Many2one('test.type',string="Test Type")

class CertificateType(models.Model):
    _name = 'certificate.type'

    name = fields.Char('Name')

class InstituteType(models.Model):
    _name = 'institute.type'

    name = fields.Char('Name')

class ParentList(models.Model):
    _name = 'parent.list'

    admission_id = fields.Many2one('op.admission',string="Admission Rel")
    name = fields.Char('Name')
    relation = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
    ], string='Relation')
    place_of_residence = fields.Many2one('res.country',string="Place Of Residence")
    work_place = fields.Char('Work Place')
    parent_mob_no = fields.Char('Mobile No')
    parent_work_phone = fields.Char('Work Tel Number')

class MultiAddress(models.Model):
    _name = 'multi.address'

    admission_id = fields.Many2one('op.admission',string="Admission Rel")
    street = fields.Char('Street',size=256)
    street2 = fields.Char('Street2',size=256)
    city = fields.Char('City',size=256)
    zip = fields.Char('Zip',size=8)
    phone = fields.Char('Phone',size=16)
    mobile = fields.Char('Mobile',size=16)
    state_id = fields.Many2one('res.country.state',string="state")
    country_id = fields.Many2one('res.country',string="Country")


class SectorType(models.Model):
    _name = 'sector.type'

    name = fields.Char('Name')

class EmployerType(models.Model):
    _name = 'employer.type'

    name = fields.Char('Name')

class CaseType(models.Model):
    _name = 'case.type'

    name = fields.Char('Name')

class TestType(models.Model):
    _name = 'test.type'

    name = fields.Char('Name')