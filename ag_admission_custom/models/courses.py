from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, fields, models, _


class CourseCustom(models.Model):
    _inherit = 'op.course'

    min_credit = fields.Float('Minimum Credit Hours')
    max_credit = fields.Float('Maximum Credit Hours')
    term_id = fields.Many2one('op.academic.term',string='Term')
    acadmic_year_id = fields.Many2one('op.academic.year',string='Academic Year')
    
class SubjectRegistrationCustom(models.Model):
    _inherit = 'op.subject.registration'

    min_credit = fields.Float('Minimum Credit Hours')
    max_credit = fields.Float('Maximum Credit Hours')
    term_id = fields.Many2one('op.academic.term',string='terms')