from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        # BUDGET OVERRIDE
        budget = self.env['crossovered.budget'].search([('state', '=', 'validate')])
        for budget_obj in budget:
            for budget_line in budget_obj.crossovered_budget_line:
                obje_position = self.env['account.budget.post'].search([('id', '=', budget_line.general_budget_id.id)])
                print("obje_position", obje_position)
                for post_id in obje_position.account_ids:
                    print("post_id", post_id)
                    for line_id in res.line_ids.account_id:
                        if line_id.id == post_id.id:
                            practical_amount = abs(budget_line.practical_amount)
                            planned_amount = budget_line.planned_amount
                            for r in res.line_ids:
                                sum = r.credit + r.debit + practical_amount
                                if abs(sum) > planned_amount:
                                    raise UserError(_('You Are Exceeding Budget Please Contact System Admin'))

        # OVERRIDE
        if any('state' in vals and vals.get('state') == 'posted' for vals in vals_list):
            raise UserError(
                _('You cannot create a move already in the posted state. Please create a draft move and post it after.'))
        vals_list = self._move_autocomplete_invoice_lines_create(vals_list)
        # return models.Model.create(self, vals_list)
        return super(AccountMove, self).create(vals_list)
