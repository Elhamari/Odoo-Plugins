# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
import time
from odoo.exceptions import UserError, AccessError, ValidationError


class CashRequisition(models.Model):
    _name = "cash.requisition"
    _inherit = 'mail.thread'
    _rec_name = 'sequence'
    _order = 'sequence desc'

    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, track_visibility='always',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))

    requisition_date = fields.Date(string="Requisition Date", required=True, track_visibility='always',default=fields.Date.today())

    state = fields.Selection([
        ('new', 'New'),
        ('department_approval', 'Waiting Department Approval'),
        ('ir_approve', 'Waiting Accounts Approved'),
        ('approved','Approved'),
        ('reject','Rejected')
        ], string='Stage', default="new")


    amount = fields.Float('Amount')

    confirmed_by_id = fields.Many2one('res.users', string="Confirmed By")
    department_manager_id = fields.Many2one('hr.employee',related='employee_id.parent_id',string="Department Manager")
    approved_by_id = fields.Many2one('res.users', string="Approved By")
    prepared_by = fields.Many2one('res.users', string="Prepared By")
    rejected_by = fields.Many2one('res.users', string="Rejected By")
    confirmed_date = fields.Date(string="Confirmed Date", readonly=True)
    department_approval_date = fields.Date(string="Department Approval Date", readonly=True)
    approved_date = fields.Date(string="Approved Date", readonly=True)
    rejected_date = fields.Date(string="Rejected Date", readonly=True)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    expense_ids = fields.One2many('hr.expense', 'cash_req_id', string='Expense')
    all_exp_count = fields.Integer(string="Expenses", compute='_compute_all_exp_count', store=True)
    employee_account_id = fields.Many2one('account.account', string="Employee Account")
    treasury_account_id = fields.Many2one('account.account', string="Cash Requisition Account")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,

                                 domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    #move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id)


    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.user.company_id.currency_id)




    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('cash.requisition') or '/'
        vals['prepared_by'] = self.env.uid
        return super(CashRequisition, self).create(vals)

    def confirm_requisition(self):
        self.ensure_one()
        res = self.write({
            'state': 'department_approval',
            'confirmed_by_id': self.env.user.id,
            'confirmed_date': datetime.now()
        })


    def action_reject(self):

        for rec in self:
            rec.write({'state': 'reject',
                       'rejected_by': self.env.user.id,
                       'rejected_date': datetime.now()
                       })

    def action_draft(self):

        for rec in self:
            rec.write({'state': 'new'})

    def department_approve(self):

        for rec in self:
            rec.write({'state': 'ir_approve',
                       'department_manager_id': self.env.user.id,
                       'department_approval_date': datetime.now()
                       })
            # # if not rec.department_manager_id:
            # #     raise ValidationError(
            # #         _("Please Assign a Department Manager or Time Off Approver to Employee.")
            # #     )
            # if rec.employee_id.parent_id.id != self.env.user.id:
            #
            #
            # else:
            #     raise ValidationError(
            #         _("Only Department Managers Can Approve.")
            #     )
            #


            #

    def action_view_cash_req(self):
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_cash_req_id': self.id,
            'default_employee_id':self.employee_id.id
            # 'default_flight_no':self.flight,
            # 'default_source':self.source_from.id,
            # 'default_destination':self.source_to.id,
            # 'default_take_of_time':self.start_time,
            # 'default_landing_time':self.end_time

        })

        return {
            'name': _('Requisition'),
            'domain': [('cash_req_id', '=', self.id)],
            'res_model': 'hr.expense',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': ctx

        }

    @api.depends('expense_ids')
    def _compute_all_exp_count(self):
        for est in self:
            est_cnt = 0
            for order in est.expense_ids:
                est_cnt += 1

            est.all_exp_count = est_cnt


    def account_approve(self,add_payment_vals={}):
        print('----journal---')
        # if not self.employee_account_id or not self.treasury_account_id or not self.journal_id:
        #     raise UserError("You must enter employee account & Treasury account and journal to approve ")


        self.ensure_one()
        partner = False
        if not self.employee_id.address_home_id.commercial_partner_id.id:
            raise UserError(
                'Please configure partner in employee master')
        else:
            partner = self.employee_id.address_home_id.commercial_partner_id.id


        payment_vals = {
            'amount': self.amount,
            'payment_type': 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': partner,
            'partner_type': 'supplier',
            'date': self.requisition_date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_line_id': self.env.ref('account.account_payment_method_manual_out').id,
            #'payment_method_id': self.env.ref('payment.use_electronic_payment_method').id,
            # 'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'ref': 'Cash Requisition' + '-' + (self.sequence),

            **add_payment_vals,
        }
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        self.write({'state': 'approved'})

        return payment







