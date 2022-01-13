from odoo.exceptions import Warning
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    # def _get_default_notice_days(self):
    #     if self.env['ir.config_parameter'].get_param(
    #             'hr_resignation.notice_period'):
    #         return self.env['ir.config_parameter'].get_param(
    #                         'hr_resignation.no_of_days')
    #     else:
    #         return 0

    notice_days = fields.Integer(string="Notice Period", default=90)
    probation_period_end_date  = fields.Date('Probation Period End Date',compute='_compute_prob_period',store=True)


    @api.depends('employee_id', 'probation_period_end_date', 'notice_days')
    def _compute_prob_period(self):
        for res in self:
            res.probation_period_end_date = False
            days = res.notice_days
            if days and days > 0:
                if res.employee_id.joining_date:
                    res.probation_period_end_date = datetime.strptime(str(res.employee_id.joining_date),
                                                                      '%Y-%m-%d') + relativedelta(
                        days=+int(days))
