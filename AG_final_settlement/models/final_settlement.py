# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta ,date
import dateutil
from dateutil import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
import math


class FinalSettlement(models.Model):
    _name = "final.settlement"
    _rec_name = 'employee_id'


    #

    @api.model
    def _default_journal(self):
        journal_type = self.env.context.get('journal_type', False)
        company_id = self.env.company.id
        if journal_type:
            journals = self.env['account.journal'].search(
                [('type', '=', journal_type), ('company_id', '=', company_id)])
            if journals:
                return journals[0]
        return self.env['account.journal']

    def create_settlement_payment(self, add_payment_vals={}):
        ''' Create an account.payment record for the current payment.transaction.

        '''
        self.ensure_one()

        payment_vals = {
            'amount': self.final_payment,
            'payment_type': 'inbound' if self.final_payment > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.employee_id.address_home_id.commercial_partner_id.id,
            'partner_type': 'supplier',
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            #'payment_method_id': self.env.ref('payment.account_payment_method_electronic_in').id,
            # 'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'ref': 'Final Settlement Payment',
            'name': self.name,
            **add_payment_vals,
        }
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment


        self.write({'state': 'paid'})

        return payment

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('settle.payment')
        # com = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        return super(FinalSettlement, self).create(vals)

    def action_generate(self):
        payable = 0
        recievable = 0
        unpaid_tot = 0
        leave_tot = 0
        tot = 0
        basic_tot = 0
        travel_tot = 0
        da_tot = 0
        working_days = 0
        amount = 0
        days_in_year = 365
        months_in_year = 12
        net_sal = 0
        payslip_date = False
        date_plus_month = False
        a_month = False
        basic_amt = 0


        for obj in self:
            final_settlement = obj.settlement_type_id.final_settlement
            leave_pending = obj.employee_id.earned_leaves_count
            joining_date = obj.employee_id.joining_date
            department = obj.employee_id.department_id.id
            job = obj.employee_id.job_id.id

            holiday_ids = self.env['hr.leave'].search([('employee_id','=',obj.employee_id.id),('holiday_status_id','=',4),('state','not in',('cancel','refuse'))])
            for holiday in holiday_ids:
                holiday_obj = self.env['hr.leave'].browse(holiday).id
                unpaid_tot = unpaid_tot + holiday_obj.number_of_days





            date_to = obj.resign_date
            if date_to:
                date_to = datetime.strptime(str(date_to),"%Y-%m-%d")
            if joining_date:
                joining_date = datetime.strptime(str(joining_date),"%Y-%m-%d")
            if not (date_to and joining_date):
                raise UserError(_('make sure joining_date and document date given'))

            working_days = ((date_to - joining_date).days + 1) - unpaid_tot
            allow_rules = []
            employee_id = obj.employee_id and obj.employee_id.id
            # if obj.employee_id.exit_progress != 100:
            # 	raise ValidationError(_('Employee has not completed exit progress'))
            contract_ids = self.env['hr.contract'].search([('employee_id','=',employee_id),('state','=','open')])
            if not contract_ids:
                raise UserError(_('no active contract for this employee'))
            contract_id = contract_ids[0]
            contract_obj = self.env['hr.contract'].browse(contract_id).id
            #basic = contract_obj.wage
            #net = contract_obj.wage
            contract_type_name = obj.employee_id.contract_id.contract_type_id.name
            #total_sal = contract_obj.hr_total_wage
            basic_tot = contract_obj.wage

            contract_lines = contract_obj.hr_allowance_line_ids
            # for contrct in contract_lines:
            #     if 'BASIC' in contrct.code:
            #         basic_amt = contrct.amt

            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', employee_id)],
                                                                  order='date_to desc', limit=1)
            if payslip_ids:
                payslip_obj = payslip_ids[-1:]
                payslip_date = payslip_obj.date_to
                print('-------PAYSLIP DATE------', payslip_date)
                payslip_lines = payslip_obj.line_ids
                for payslip in payslip_lines:
                    if 'NET' in payslip.code:
                        net_sal = net_sal + payslip.amount

            if payslip_date:

                payslip_date += timedelta(days=1)
                #date_plus_month = payslip_date + a_day
                self.pending_date_from = payslip_date #.replace(day=1)
                print('-----PENDING DATE----',self.pending_date_from)
                #payslip_date = self.env.cr.execute("""Select MAX(date_from) FROM hr_payslip where employee_id = 1798 """)





            self.fs_gross_per_day = (basic_tot/30)




            vals = {

                    'contract_type_id':contract_type_name,
                    'join_date':joining_date,
                    #'total_salary':total_sal,
                    'basic':basic_tot,
                    'total_net_salary':net_sal,
                    'available_days':leave_pending,
                    'department_id':department,
                    'job_id':job,
                    #'leave_pending':leave_tot,
                    #'unpaid_leaves':unpaid_tot,
                    #'leave_pending_balance':leave_balances,
                    'total_working_days':working_days,


                    # 'job_id':obj.employee_id.job_id.id,
                    # 'department_id':obj.employee_id.department_id.id,
                    #'address_home_id':obj.employee_id.address_home_id.id,
                    }
            self.write(vals)



        return True

    #
    def action_final_settlement(self):

        final_pay = 0

        for obj in self:


            final_pay = (obj.final_settlement_amount + obj.fs_gross_available_days + obj.total_add_amt + obj.pending_leave_sal) - obj.total_dec_amt

            vals={
                #'final_settlement_amount': final_due_amt,
                'final_payment': final_pay,
                }
            self.write(vals)
            return True

    @api.onchange('resign_date')
    def onchange_resign(self):
        for rec in self:
            if rec.resign_date:
                rec.pending_date_to = rec.resign_date
            else:
                rec.pending_date_to = False

    @api.depends('pending_date_from','pending_date_to','fs_gross_per_pending_day','basic')#,'total_salary')
    def action_calc_pending_sal(self):
        p1 = self.pending_date_from
        p2 = self.pending_date_to
        days_of_month = 30
        self.duration = False

        if p1 and p2:
            p1 = datetime.strptime(str(p1), "%Y-%m-%d")
            p2 = datetime.strptime(str(p2), "%Y-%m-%d")

            delta = p2 - p1

            self.duration = delta.days + 1

            self.fs_gross_per_pending_day = self.basic / days_of_month

            self.pending_leave_sal = self.fs_gross_per_pending_day * self.duration


    @api.depends('resign_date', 'join_date', 'last_vacation','fs_gross_per_day','employee_id')
    def action_fs_date_diff(self):

        d3 = self.join_date
        d4 = self.resign_date
        #d5 = self.last_vacation
        days_in_year = 365
        months_in_year = 12
        leaves_per_month = 2.5
        days_in_month = 30
        bal_leave = 0.0


        if d3 and d4:
            d3 = datetime.strptime(str(d3), "%Y-%m-%d")
            d4 = datetime.strptime(str(d4), "%Y-%m-%d")

            # r2 relativedelta ----->   relativedelta(years=+1, months=+11, days=+30)
            r2 = relativedelta.relativedelta(d4, d3)
            print('--------------------r2--------------', r2)
            self.fs_temp_year = r2.years
            print('--------------------fs_tmp_yr--------------', self.fs_temp_year)
            # self.fs_temp_day = r2.days+(r2.months*days_in_month)
            self.fs_temp_day = (d4 - (d3 + relativedelta.relativedelta(years=r2.years))).days + 1
            print('--------------------fsday_tmp_--------------', self.fs_temp_day)
            self.fs_total_period = str(self.fs_temp_year) + ' year(s) ' + str(self.fs_temp_day) + ' day(s)'
            print('--------------------fs_total_period--------------', self.fs_total_period)


        # if d5:
        # 	d5 = datetime.strptime(str(d5), "%Y-%m-%d")
        # 	print('----d5----',d5)
        # 	delta = d4 - d5
        # 	r3 = delta.days + 1
        # 	print('--------D5-----------',d5)
        # 	print('----------D4------',d4)
        #
        # 	self.available_days = r3
        # 	print('------------available_days------------', self.available_days)

        self.fs_gross_available_days = self.fs_gross_per_day * self.available_days
        print('------------tot salary------------', self.fs_gross_available_days)

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Check whether any settlement request already exists
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['final.settlement'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['progress', 'done','paid'])])
                if resignation_request:
                    raise ValidationError(_('There is a settlement request already created for this employee'
                                            ))
            # if rec.employee_id:
            #     no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            #     for contracts in no_of_contract:
            #         if contracts.state == 'open':
            #             rec.employee_contract = contracts.name
            #             rec.notice_period = contracts.notice_days


    def action_progress(self):
        res = self.write({'state': 'progress'})
        return res

    def action_approve(self):
        for rec in self:
            #rec.employee_id.compute_resign = True
            #if rec.resign_date <= fields.Date.today() and rec.employee_id.active:
            rec.employee_id.active = False
                # Changing fields in the employee table with respect to resignation
            rec.employee_id.resign_date = rec.resign_date
                # if rec.resignation_type == 'resigned':
                #     rec.employee_id.resigned = True
                # else:
                #     rec.employee_id.fired = True
                # Removing and deactivating user
            no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            for contracts in no_of_contract:
                contracts.state = 'cancel'
            if rec.employee_id.user_id:
                rec.employee_id.user_id.active = False
                rec.employee_id.user_id = None
            res = rec.write({'state': 'done'})
            return res

    def action_reject_wizard(self):
        return {
            'name': "Refuse reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refuse.reason.settle',
            'view_id': self.env.ref('AG_final_settlement.refuse_reason_settle_view_form').id,
            'target': 'new'
        }


    def action_reject(self):
        self.write({'state': 'reject'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for pay in self:
            if pay.state in ['done', 'paid']:
                raise UserError(_('You cannot delete a posted or approved settlement.'))
        return super(FinalSettlement, self).unlink()

    #
    def action_validate(self):
        for obj in self:
            if not obj.account_new_line:
                raise UserError(_('there is no lines in adjustment'))
            final_settlement = obj.final_settlement
            account_move_obj = self.env['account.move']
            journal_id = obj.settlement_type_id.journal_id and obj.settlement_type_id.journal_id.id
            home_address = obj.employee_id.address_home_id and obj.employee_id.address_home_id.id
            date = obj.resign_date
            total_credit = 0
            total_debit = 0
            narration = 'Final Settlement' + '/'+ str(obj.employee_id.name)
            # period_pool = self.pool.get('account.period')
            # search_periods = period_pool.find(cr, uid, date, context=context)
            # period_id = search_periods[0]
            data_lines = []

            if not home_address:
                raise UserError(_('pls define partner for the employee'))

            recievable_acc_id = obj.employee_id.address_home_id.property_account_receivable_id and obj.employee_id.address_home_id.property_account_receivable_id.id
            payable_acc_id = obj.employee_id.address_home_id.property_account_payable_id and obj.employee_id.address_home_id.property_account_payable_id.id
            if not payable_acc_id:
                raise UserError(_('set payable acc in employee home address'))
            if not recievable_acc_id:
                raise UserError(_('set recievable acc in employee home address'))

            for lines in obj.account_new_line:
                total_debit = total_debit + round(lines.debit,2)
                total_credit = total_credit + round(lines.credit,2)

            if total_debit != total_credit:

                raise UserError(_('total debit and credit are not matching'))


            for line in obj.account_new_line:

                vals2 = {
                        'journal_id':journal_id,
                        'date':date,
                        'naration':narration,
                        'name':narration,
                        'account_id':line.account_id.id,
                        'debit':line.debit,
                        'credit':0.0,
                        'partner_id':home_address,
                }
                if vals2['debit'] >0.0 or vals2['credit'] >0.0:
                    data_lines.append((0,0,vals2),)


                vals1 = {
                        'journal_id':journal_id,
                        'date':date,
                        'naration':narration,
                        'name':narration,
                        'account_id':line.account_id.id,
                        'debit':0.0,
                        'credit':line.credit,
                        'partner_id':home_address,
                }
                if vals1['debit'] >0.0 or vals1['credit'] >0.0:
                    data_lines.append((0,0,vals1),)


            if data_lines:
                data = {
                    'journal_id':journal_id,
                    'date':date,
                    'state':'draft',
                    'ref':narration,
                    'line_ids':data_lines
                }
                account_move = account_move_obj.create(data)

                self.write({'state':'done','account_move_id':account_move.id})
            else:
                raise UserError(_('no lines for generating journal entry'))

        return True


    #
    def check_accounts_entry(self):
        for obj in self:
            final_settlement = obj.final_settlement
            extra_row = {}
            transaction_ids = []
            recievable_acc_id = obj.employee_id.address_id.property_account_receivable_id and obj.employee_id.address_id.property_account_receivable_id.id
            payable_acc_id = obj.employee_id.address_id.property_account_payable_id and obj.employee_id.address_id.property_account_payable_id.id
            debit = 0
            credit = 0
            total_due = 0
            total_amt = 0
            total_debit =0
            total_credit =0
            sum_of_negative_values = 0
            sum_of_postive_values = 0
            existing_ids = self.env['final.settlement.new.account.line'].search([('account_line_id','=',obj.id)])
            if existing_ids:
                self.env['final.settlement.new.account.line'].unlink()

            for linee in obj.account_line:
                transaction_ids.append(linee.id)
            if not transaction_ids:
                raise UserError(_('generate the transactions first'))




            for line in obj.account_line:
    #            if not obj.account_line:
    #                raise osv.except_osv(_('Warning!'), _('generate the transactions first'))

                total_due = total_due + line.balance
                total_amt = total_amt + line.amount
                if line.balance < 0:

                    if line.amount <0:
                        sum_of_negative_values = sum_of_negative_values + line.balance
                        raise UserError(_('check the signs of balance and amount'))

                if line.balance > 0:
                    if line.amount >0:
                        sum_of_postive_values = sum_of_postive_values + line.balance
                        raise UserError(_('check the signs of balance and amount'))

                    credit = line.amount

                    debit = 0
                else:
                    credit = 0
                    debit = line.amount
                print("::::::::::::sum_of_postive_values",sum_of_postive_values)
                print("::::::::::::sum_of_negative_values",sum_of_negative_values)
                vals = {'account_id':line.account_id.id or False,'account_line_id':line.account_line_id.id or False,'final_settlement':final_settlement,'debit':math.fabs(debit),'credit':math.fabs(credit),'due':math.fabs(line.balance)}
                self.env['final.settlement.new.account.line'].create(vals)
            if total_due < 0:
                total_debit = 0
                total_credit =total_amt

                extra_row = {'account_id':payable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
            else:
                total_debit = total_amt
                total_credit =0
                extra_row = {'account_id':recievable_acc_id or False,'account_line_id':obj.id or False,'final_settlement':final_settlement,'debit':math.fabs(total_debit),'credit':math.fabs(total_credit)}
            self.env['final.settlement.new.account.line'].create(extra_row)
            self.write({'state':'progress'})
        return True

    #
    def generate_gratuity_value(self):
        experience = 0
        gratuity = 0
        for obj in self:
            obj.gratuity_line_id.unlink()
            terminated = obj.settlement_type_id.termination
            resign = obj.settlement_type_id.final_settlement
            join_date = obj.join_date
            resign_date = obj.resign_date
            # raise UserError(_(obj.join_date))
            if not obj.join_date:
                raise UserError(_("pls provide join date"))
            joining_date = datetime.strptime(str(join_date), "%Y-%m-%d").date()
            gratuity_date = datetime.strptime(str(resign_date), "%Y-%m-%d").date()
            experience = float((gratuity_date -  joining_date).days)/365.00
            experiance_days = float((gratuity_date -  joining_date).days)
            working_days = ((gratuity_date - joining_date).days + 1)
            contract_ids = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','=','open')])
            if not contract_ids:
                raise UserError(_('no active contract for this employee'))
            contract_ids = contract_ids[0]
            contract_obj = self.env['hr.contract'].browse(contract_ids).id
            contract_type = contract_obj.contract_type_id.name
            one_day_wage = float(contract_obj.wage * 12) / 365.00
            max_gratuity = float(contract_obj.wage * 24)
#                 one_day_wage = float((contract_obj.wage) / 30)


##################################################case1
            data_lines = []
            if contract_type =='limited' and resign==True:
                if experience < 1:
                    vals1 = {
                              'slab':'0 to 1 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0.0,
                              'resign_amount':0.0,
                    }
                    data_lines.append((0,0,vals1),)
                elif experience >= 1 and experience < 3:
                    gratuity = (((7 * one_day_wage)/365.0) * experiance_days)
                    vals2 = {
                              'slab':'1 to 3 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals2),)
                elif experience >= 3 and experience < 5:
                    gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
                    vals3 = {
                              'slab':'3 to 5 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals3),)
                elif experience >= 5:
                    extra_year = experience - 5
                    extra_year_in_days = extra_year * 365
                    gratuity = ((21 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
                    vals4 = {
                              'slab':'Over 5 Years',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals4),)
                self.gratuity_line_id = data_lines

            if contract_type =='limited' and terminated==True:
                if experience < 1:
                    vals1 = {
                              'slab':'0 to 1 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0.0,
                              'resign_amount':0.0,
                    }
                    data_lines.append((0,0,vals1),)
                elif experience >= 1 and experience < 3:
                    gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
                    vals2 = {
                              'slab':'1 to 3 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals2),)
                elif experience >= 3 and experience < 5:
                    gratuity = (((21 * one_day_wage)/365.0) * experiance_days)
                    vals3 = {
                              'slab':'3 to 5 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals3),)
                elif experience >= 5:
                    extra_year = experience - 5
                    extra_year_in_days = extra_year * 365
                    gratuity = ((30 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
                    vals4 = {
                              'slab':'Over 5 Years',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals4),)
                self.gratuity_line_id = data_lines
            if contract_type =='unlimited' and resign==True:
                if experience < 1:
                    vals1 = {
                              'slab':'0 to 1 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0.0,
                              'resign_amount':0.0,
                    }
                    data_lines.append((0,0,vals1),)
                elif experience >= 1 and experience < 3:
                    gratuity = (((7 * one_day_wage)/365.0) * experiance_days)
                    vals2 = {
                              'slab':'1 to 3 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals2),)
                elif experience >= 3 and experience < 5:
                    gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
                    vals3 = {
                              'slab':'3 to 5 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals3),)
                elif experience >= 5:
                    extra_year = experience - 5
                    extra_year_in_days = extra_year * 365
                    gratuity = ((21 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
                    vals4 = {
                              'slab':'Over 5 Years',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0,
                              'resign_amount':gratuity,
                    }
                    data_lines.append((0,0,vals4),)
                self.gratuity_line_id = data_lines

            if contract_type =='unlimited' and terminated==True:
                if experience < 1:
                    vals1 = {
                              'slab':'0 to 1 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':0.0,
                              'resign_amount':0.0,
                    }
                    data_lines.append((0,0,vals1),)
                elif experience >= 1 and experience < 3:
                    gratuity = (((14 * one_day_wage)/365.0) * experiance_days)
                    vals2 = {
                              'slab':'1 to 3 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals2),)
                elif experience >= 3 and experience < 5:
                    gratuity = (((21 * one_day_wage)/365.0) * experiance_days)
                    vals3 = {
                              'slab':'3 to 5 Year',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals3),)
                elif experience >= 5:
                    extra_year = experience - 5
                    extra_year_in_days = extra_year * 365
                    gratuity = ((30 * one_day_wage)*5) + (((one_day_wage *30) /365) * extra_year_in_days)
                    vals4 = {
                              'slab':'Over 5 Years',
                              'date_from':joining_date,
                              'date_to':gratuity_date,
                              'no_of_days':working_days,
                              'termination_amount':gratuity,
                              'resign_amount':0,
                    }
                    data_lines.append((0,0,vals4),)
                self.gratuity_line_id = data_lines

        return True

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    name = fields.Char(string='Code', copy=False, help="Code")

    join_date = fields.Date('Join Date',store=True)
    resign_date = fields.Date(string="Resign Date", default=fields.Date.context_today)
    last_date = fields.Date(string="Last Working Date")
    settlement_type_id = fields.Many2one('final.settlement.type.master',string="Settlement Type",required=True)
    basic = fields.Float(string="Basic Salary")
    hra = fields.Float(string="HRA")
    da = fields.Float(string="DA")
    travel = fields.Float(string="Travel")
    #resignation_id = fields.Many2one('hr.resignation', string='Resignation')
    #fs_allowance = fields.Float('Allowance', states={'draft': [('readonly', False)]}, readonly=True)
    fs_gross_per_day = fields.Float('Per Day Annual leave Salary', states={'draft': [('readonly', False)]},
                                    readonly=True)
    #hr_allowance_line_ids = fields.One2many('hr.allowance.line','nn_sett_id',string="HR Allowance")
    #total_salary = fields.Float('Total Salary')
    payroll_overtime = fields.Float('Overtime')
    payroll_ded = fields.Float('Deductions')
    payroll_add = fields.Float('Additions')
    payroll_allw = fields.Float('Allowances')

    total_net_salary = fields.Float('Net Salary')
    final_settlement_amount = fields.Float('Gratuity Amount',compute='_get_gratuity_amt',store=True)
    final_payment = fields.Float('Final payment',store=True)
    department_id = fields.Many2one('hr.department',string="Department",readonly=True)
    job_id =fields.Many2one('hr.job',string='Job', readonly=True)
    contract_type_id = fields.Char(string='Contract Type')
    fs_temp_year = fields.Float('temp year', states={'draft': [('readonly', False)]}, readonly=True)
    fs_temp_day = fields.Integer('temp day', states={'draft': [('readonly', False)]}, readonly=True)
    fs_total_period = fields.Char('Job Duration', states={'draft': [('readonly', False)]}, readonly=True)
    fs_temp_month_2 = fields.Float('temp month', states={'draft': [('readonly', False)]}, readonly=True)
    available_days = fields.Float('Balance Leaves',store=True)
    fs_gross_available_days = fields.Float('Eligible Leave Salary', states={'draft': [('readonly', False)]},
                                           readonly=True)
    pending_leave_sal = fields.Float('Pending Salary', states={'draft': [('readonly', False)]},
                                           readonly=True)

    pending_date_from = fields.Date('Pending Salary Dates',store=True)
    pending_date_to = fields.Date('Pending Date To',store=True)
    duration = fields.Integer('Duration', store=True)
    fs_gross_per_pending_day = fields.Float('Per Day Salary', states={'draft': [('readonly', False)]},
                                    readonly=True)
    refuse_reason = fields.Text('Rejection reason')

    reason = fields.Text(string="Reason")
    state = fields.Selection([
            ('draft', 'New'),
            ('progress', 'Progress'),
            ('done', 'Done'),
            ('reject','Rejected'),
            ('paid','Paid')
            ],
            'Status', readonly=True, default='draft',track_visibility='onchange')
    final_settlement = fields.Boolean("Final Settlement")
    address_home_id = fields.Many2one('res.partner', string='Home Address',readonly=True)
    account_line = fields.One2many('final.settlement.account.line','account_line_id',string="Account Line")
    account_new_line = fields.One2many('final.settlement.new.account.line','account_line_id',string="Account New Line")
    account_move_id = fields.Many2one('account.move','Entry',readonly=True)
    gratuity_line_id = fields.One2many('gratuity.employee','settlement_grat_id',string="Gratuity Line")
    payroll_trans_line = fields.One2many('payslip.transaction','settlement_trans_id',string='Payroll Transaction Line')
    total_dec_amt = fields.Float('Total Deductions', compute="_total_payroll_wage")
    total_add_amt = fields.Float('Total Additions', compute="_total_payroll_wage")

    #leave_pending = fields.Integer(string="Remaining Annual Leaves")
    #leave_pending_balance = fields.Float(string='Leave Balance Amount')
    last_vacation = fields.Date('Last Vacation End Date')
    #unpaid_leaves = fields.Integer(string="Unpaid Leaves")
    total_working_days = fields.Float(string="Total Working Days")
    payslip_ids = fields.One2many('hr.payslip', 'settle_id', string='Payslip')

    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id)

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.user.company_id.currency_id)

    journal_id = fields.Many2one('account.journal', string='Journal', default=_default_journal,
                                 check_company=True)

    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True)

    date = fields.Date(readonly=True, default=fields.Date.context_today,
                       string="Date")
    # @api.depends('employee_id')
    # def calculate_acc(self):

    def action_view_payslip(self):
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_employee_id': self.employee_id.id,
            'default_settle_id': self.id,
        })

        return {
            'name': _('Payslips'),
            'domain': [('settle_id', '=', self.id)],
            'res_model': 'hr.payslip',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': ctx

        }

    @api.depends('payroll_trans_line','total_dec_amt','total_add_amt')
    def _total_payroll_wage(self):
        x = 0
        y = 0
        for rec in self:

            for l in rec.payroll_trans_line:
                if l.payroll_item == 'add':
                    x = x + l.amount
                elif l.payroll_item == 'ded':
                    y = y + l.amount
                else:
                    x = 0
                    y = 0
            rec.total_add_amt = x
            rec.total_dec_amt = y

    @api.depends('final_settlement_amount','gratuity_line_id')
    def _get_gratuity_amt(self):
        final_due_amt = 0
        for obj in self:

            if not obj.gratuity_line_id:
                print('no lines')
                #raise UserError(_('there is no lines in gratuity'))

            if obj.gratuity_line_id.resign_amount:
                final_due_amt = obj.gratuity_line_id.resign_amount
            elif obj.gratuity_line_id.termination_amount:
                final_due_amt = obj.gratuity_line_id.termination_amount

            obj.final_settlement_amount = final_due_amt


    # @api.onchange('employee_id')
    # @api.depends('employee_id')
    # def _change_employee(self):
    # 	for rec in self:
    # 		rec.join_date = fields.Datetime.to_string(rec.employee_id.joining_date)
    # 		rec.department_id = rec.employee_id.department_id
    # 		rec.job_id = rec.employee_id.job_id
    # 		rec.contract_type_id = rec.employee_id.contract_id.contract_type

            # annual_tot = 0
            # leave_type = self.env['hr.leave.type'].search([('code', '=', 'ANNUAL')])
            # # print('----leavtye---',leave_type.mapped(id))
            # annual_new = False
            #
            # for type in leave_type:
            # 	annual_new = type.name
            #
            # leave_type_name = annual_new
            # print('leave_type_name',leave_type_name)
            # leave_records = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id),
            # 											 ('state', '=', 'validate'),
            # 											 ('holiday_status_id', 'in', 'leave_type_name')],
            # 											order='request_date_to desc', limit=1)
            # lv = leave_records
            # print('----lv----',lv)
            # rec.last_vacation = lv.request_date_to


# class HRallowanceLine(models.Model):
#     _inherit = 'hr.allowance.line'

#     nn_sett_id = fields.Many2one('final.settlement',string="Settlement")

class FinalSettlementAccountLine(models.Model):
    _name = "final.settlement.account.line"
    _description = "final.settlement.account.line"



    account_line_id = fields.Many2one('final.settlement',"settlement")
    account_id = fields.Many2one('account.account',"Account",required=True)
    balance = fields.Float("Balance",readonly=True)
    amount = fields.Float("Payable")
    final_settlement_flag = fields.Boolean("Final Settlement")




class od_final_settlement_new_account_line(models.Model):
    _name = "final.settlement.new.account.line"
    _description = "final.settlement.new.account.line"

    # def create(self, cr, uid, vals, context=None):
    #     if vals.get('account_line_id') or  vals.get('account_id'):
    #         obj = self.pool.get('od.final.settlement').browse(cr,uid,[vals.get('account_line_id')],context)
    #         final_settlement = obj.final_settlement


    #         if final_settlement:
    #             vals['final_settlement'] = final_settlement
    #     return super(od_final_settlement_new_account_line, self).create(cr, uid, vals, context=context)




    account_line_id = fields.Many2one('final.settlement',string="Settlement")
    account_id = fields.Many2one('account.account',string="Account",required=True)
    debit = fields.Float("Debit")
    credit = fields.Float("Credit")
    due = fields.Float("Due")
    final_settlement = fields.Boolean("Final Settlement")



class FinalSettlementTypeMaster(models.Model):
    _name = "final.settlement.type.master"

    name = fields.Char("Name",required=True)
    final_settlement = fields.Boolean("Resign")
    remarks = fields.Text("Remarks")
    termination = fields.Boolean("Termination")
    journal_id = fields.Many2one('account.journal',string="Journal")
    settlement_type_master_line = fields.One2many('final.settlement.type.master.line','settlement_type_master_line_id',string="Settlement Line")

class FinalSettlementTypeMasterLine(models.Model):
    _name = "final.settlement.type.master.line"


    account_id = fields.Many2one('account.account',"Account")
    settlement_type_master_line_id = fields.Many2one('final.settlement.type.master')


class GratuityCalculation(models.Model):
    _name = "gratuity.employee"


    slab = fields.Char(string="Slab")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    no_of_days = fields.Float(string="Num of Days Working")
    termination_amount = fields.Float(string="Termination")
    resign_amount = fields.Float(string="Resignation")
    settlement_grat_id = fields.Many2one('final.settlement', string="Settlement")




# class Contract(models.Model):
# 	_inherit = 'hr.contract'
#
# 	contract_type = fields.Selection([('limited', 'Limited'),('unlimited', 'Unlimited')], string="Contract Type", required=True)
#


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    settle_id = fields.Many2one(
        'final.settlement', string='Settlement')

    pay_true = fields.Boolean('Created From Settlement',compute='_compute_pay_true')

    @api.depends('pay_true','settle_id')
    def _compute_pay_true(self):
        if self.settle_id:
            self.pay_true = True
        else:
            self.pay_true = False


class AdditionDedCalculation(models.Model):
    _name = "payslip.transaction"

    settlement_trans_id = fields.Many2one('final.settlement')
    tran_note = fields.Char('Description')
    amount = fields.Float('Amount')
    payroll_item = fields.Selection([('add', 'Additions'),('ded', 'Deductions')],'Transactions', required=True, track_visibility='onchange')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resign_date = fields.Date('Resign Date', readonly=True, help="Date of the resignation")
    resigned = fields.Boolean(string="Resigned", default=False, store=True,
                              help="If checked then employee has resigned")
    fired = fields.Boolean(string="Fired", default=False, store=True, help="If checked then employee has fired")
