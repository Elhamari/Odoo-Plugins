
from odoo import models, fields, api, exceptions, _

class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'

    hr_allowance_line_ids = fields.One2many('hr.allowance.line', 'contract_id', string='HR Allowance')
    hr_total_wage = fields.Float('Total Salary', compute="_total_wage")
    amount_in_word = fields.Char('Amount in Word', compute="_get_amount_inword")



    # @api.multi
    def _total_wage(self):
        for rec in self:
            x = rec.wage
            for l in rec.hr_allowance_line_ids:
                x = x + l.amt
            rec.hr_total_wage = x

    @api.depends('hr_total_wage', 'currency_id')
    def _get_amount_inword(self):
        self.amount_in_word = self.currency_id.amount_to_text(self.hr_total_wage) if self.currency_id else ''
        unit = self.currency_id.currency_unit_label
        subunit = self.currency_id.currency_subunit_label
        self.amount_in_word = self.amount_in_word.replace(' %s ' % unit, ' ').replace(' %s' % unit, ' ').replace(
            ' And ', ' ').replace(',', ' ')


class HRallowanceLine(models.Model):
    _name = 'hr.allowance.line'

    contract_id = fields.Many2one('hr.contract')
    rule_type = fields.Many2one('hr.salary.rule', string="Allowance Rule")
    code = fields.Char('Code', related="rule_type.code", store=True, readonly=True)
    amt = fields.Float('Amount')


class MultiPaySlipWiz(models.TransientModel):
    _name = 'multi.payslip.wizard'
    _description = 'Multi Pay Slip Wiz'

    def multi_payslip(self):
        payslip_ids = self.env['hr.payslip']. \
            browse(self._context.get('active_ids'))
        for payslip in payslip_ids:
            if payslip.state in ['verify', 'draft']:
            	payslip.compute_sheet()
            	payslip.action_payslip_done()
