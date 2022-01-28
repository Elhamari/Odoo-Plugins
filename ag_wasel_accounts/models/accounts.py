from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Analatic Accounts Changes
class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'


    analytic_code = fields.Char('Code',copy=False)

    _sql_constraints = [
        ('analytic_code_uniq', 'unique (analytic_code)', 'The code of the analytic account must be unique!')
    ]

class AnalyticAccountTag(models.Model):
    _inherit = 'account.analytic.tag'


    total_percent = fields.Float('Total Percentage',compute='_onchange_analytic_tag',store=True,)

    @api.depends('analytic_distribution_ids')
    def _onchange_analytic_tag(self):
        for rec in self:
            if rec.analytic_distribution_ids:
                if sum(rec.analytic_distribution_ids.mapped('percentage')) > 100.00:
                    
                    raise UserError('The total of the percentage values should be 100 \n pls make sure the total is equal 100%')
                else:
                    rec.total_percent = sum(rec.analytic_distribution_ids.mapped('percentage'))
            else:
                rec.total_percent = 0.0

class AnalyticAccountTag(models.Model):
    _inherit = 'account.analytic.distribution'

    percentage = fields.Float(string='Percentage', required=True, default=0.0)


# ######################################################
# Budgets Changes
class Budgets(models.Model):
    _inherit = 'crossovered.budget.lines'


    def _compute_percentage(self):
        for line in self:
            if line.practical_amount != 0.00:
                line.percentage = abs(float((line.practical_amount or 0.0)) / line.planned_amount)
            else:
                line.percentage = 0.00

    @api.depends('date_from', 'date_to')
    def _compute_theoritical_amount(self):
        # beware: 'today' variable is mocked in the python tests and thus, its implementation matter
        today = fields.Date.today()
        for line in self:
            if line.paid_date:
                if today <= line.paid_date:
                    theo_amt = 0.00
                else:
                    theo_amt = line.planned_amount
            else:
                if not line.date_from or not line.date_to:
                    line.theoritical_amount = 0
                    continue
                # One day is added since we need to include the start and end date in the computation.
                # For example, between April 1st and April 30th, the timedelta must be 30 days.
                line_timedelta = line.date_to - line.date_from + timedelta(days=1)
                elapsed_timedelta = today - line.date_from + timedelta(days=1)

                if elapsed_timedelta.days < 0:
                    # If the budget line has not started yet, theoretical amount should be zero
                    theo_amt = 0.00
                elif line_timedelta.days > 0 and today < line.date_to:
                    # If today is between the budget line date_from and date_to
                    theo_amt = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                else:
                    theo_amt = line.planned_amount
            line.theoritical_amount = 0.00
        

# ######################################################
# Assets Changes
class AccountAsset(models.Model):
    _inherit = "account.asset"

    asset_code = fields.Char('Asset Code')

    _sql_constraints = [
        ('asset_code_uniq', 'unique (asset_code)', 'The code of the asset must be unique!')
    ]
# ######################################################
# PO-Accounts Related Changes
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        res = super(PurchaseOrder,self)._prepare_invoice()
        res['invoice_date'] = self.effective_date
        res['date'] = self.effective_date
        return res
