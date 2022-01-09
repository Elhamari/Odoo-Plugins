from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError



class HrLeave(models.Model):
    _inherit = "hr.leave"

    joining_date = fields.Date(string='Join Date', related='employee_id.joining_date', store=True)
    one_yr_calc_date = fields.Date(
        'Completed One Year?', readonly=True, index=True, copy=False, compute='_compute_one_year',tracking=True)





    @api.depends('joining_date', 'request_date_from')
    def _compute_one_year(self):
        for rec in self:

            if rec.joining_date:
                rec.one_yr_calc_date = rec.joining_date + timedelta(days=365)
            else:
                rec.one_yr_calc_date = False

    @api.constrains("request_date_from", "one_yr_calc_date")
    def _check_join_dates(self):
        for date in self:
            if date.request_date_from and date.one_yr_calc_date and date.request_date_from < date.one_yr_calc_date:
                raise ValidationError(
                    _("Employee is not eligible for annual leaves, since he has not completed one year.")
                )
