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

    @api.model_create_multi
    def create(self, vals):
        percent = 0.0
        res = super(AnalyticAccountTag, self).create(vals)
        if res.analytic_distribution_ids:
            for line in res.analytic_distribution_ids:
                percent += line.percentage
            if percent != 100:
                raise UserError('The total of the percentage values should be 100%')
        return res


    def write(self, vals):
        percent = 0.0
        res = super(AnalyticAccountTag, self).write(vals)
        if self.analytic_distribution_ids:
            for line in self.analytic_distribution_ids:
                percent += line.percentage
            if percent != 100:
                raise UserError('The total of the percentage values should be 100%')
        return res
        
        
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



#######################################################
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_budget_approval = fields.Boolean(related='company_id.po_budget_approval', string="Purchase Order Budget Approval", readonly=False)

class Company(models.Model):
    """ Default  accounts and journals part"""
    _inherit = "res.company"

    po_budget_approval = fields.Boolean(string='Purchase Order Budget Approval',
        help="Minimum amount for which a double validation is required")
        
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


    def button_confirm(self):
        order_list=[]
        for order in self:
            if self.env.company.po_budget_approval is True:
                for line in self.order_line:
                    order_list.append({'account_id':line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id, 'analytic_id':line.account_analytic_id.id, 'price_subtotal':line.price_subtotal})
                budget = self.env['crossovered.budget'].search([('state', '=', 'validate')])
                for budget_obj in budget:
                    for budget_line in budget_obj.crossovered_budget_line:
                        for a in order_list:
                            if budget_line.general_budget_id.account_ids.id == a['account_id'] and budget_line.analytic_account_id.id == a['analytic_id']:
                                if (budget_line.planned_amount - budget_line.practical_amount)  < a['price_subtotal']  and not self.env.user.has_group('ag_wasel_accounts.group_purchase_budget_user'):
                                    raise UserError(_('This document need to confirmed by the manager becuase it exceeded the budget amount'))
                                        
                                    
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True
        
        
    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        res = super(PurchaseOrder,self)._prepare_invoice()
        res['invoice_date'] = self.effective_date
        res['date'] = self.effective_date
        return res
