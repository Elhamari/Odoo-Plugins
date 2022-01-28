from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta , date

# class AccountPaymentInvoices(models.Model):
#     _name = 'account.payment.invoice'

#     invoice_id = fields.Many2one('account.move', string='Invoice')
#     payment_id = fields.Many2one('account.payment', string='Payment')
#     currency_id = fields.Many2one(related='invoice_id.currency_id')
#     origin = fields.Char(related='invoice_id.invoice_origin')
#     date_invoice = fields.Date(related='invoice_id.invoice_date')
#     date_due = fields.Date(related='invoice_id.invoice_date_due')
#     payment_state = fields.Selection(related='payment_id.state', store=True)
#     reconcile_amount = fields.Monetary(string='Reconcile Amount')
#     amount_total = fields.Monetary(related="invoice_id.amount_total")
#     residual = fields.Monetary(related="invoice_id.amount_residual")
#     allocation = fields.Boolean('Allocation',default=False)

#     @api.onchange('allocation')
#     def allocate(self):
#         for rec in self:
#             if rec.allocation == True:
#                 rec.reconcile_amount = rec.residual
#             else:
#                 rec.reconcile_amount = 0.0


# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'

#     invoice_id = fields.Many2one('account.move', string='Invoice')

#     def reconcile(self):
#         ''' Reconcile the current move lines all together.
#         :return: A dictionary representing a summary of what has been done during the reconciliation:
#                 * partials:             A recorset of all account.partial.reconcile created during the reconciliation.
#                 * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile
#                                         in the involved lines.
#                 * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries.
#         '''
#         results = {}

#         if not self:
#             return results

#         # List unpaid invoices
#         not_paid_invoices = self.move_id.filtered(
#             lambda move: move.is_invoice(include_receipts=True) and move.payment_state not in ('paid', 'in_payment')
#         )

#         # ==== Check the lines can be reconciled together ====
#         company = None
#         account = None
#         print("===self==", self)
#         for line in self:
#             if line.reconciled:
#                 raise UserError(_("You are trying to reconcile some entries that are already reconciled."))
#             if not line.account_id.reconcile and line.account_id.internal_type != 'liquidity':
#                 raise UserError(_("Account %s does not allow reconciliation. First change the configuration of this account to allow it.")
#                                 % line.account_id.display_name)
#             if line.move_id.state != 'posted':
#                 raise UserError(_('You can only reconcile posted entries.'))
#             if company is None:
#                 company = line.company_id
#             elif line.company_id != company:
#                 raise UserError(_("Entries doesn't belong to the same company: %s != %s")
#                                 % (company.display_name, line.company_id.display_name))
#             if account is None:
#                 account = line.account_id
#             elif line.account_id != account:
#                 raise UserError(_("Entries are not from the same account: %s != %s")
#                                 % (account.display_name, line.account_id.display_name))

#         sorted_lines = self.sorted(key=lambda line: (line.date_maturity or line.date, line.currency_id))

#         # ==== Collect all involved lines through the existing reconciliation ====

#         involved_lines = sorted_lines
#         involved_partials = self.env['account.partial.reconcile']
#         current_lines = involved_lines
#         current_partials = involved_partials
#         while current_lines:
#             current_partials = (current_lines.matched_debit_ids + current_lines.matched_credit_ids) - current_partials
#             involved_partials += current_partials
#             current_lines = (current_partials.debit_move_id + current_partials.credit_move_id) - current_lines
#             involved_lines += current_lines

#         # ==== Create partials ====

#         partial_amount = self.env.context.get('amount', False)
#         if partial_amount:
#             reconcile = sorted_lines._prepare_reconciliation_partials()
#             reconcile[0].update({
#                 'amount': partial_amount, 
#                 'debit_amount_currency': partial_amount, 
#                 'credit_amount_currency': partial_amount,
#             })
#         else:
#             reconcile = sorted_lines._prepare_reconciliation_partials()

#         partials = self.env['account.partial.reconcile'].create(reconcile)
#         # Track newly created partials.
#         results['partials'] = partials
#         involved_partials += partials

#         # ==== Create entries for cash basis taxes ====

#         is_cash_basis_needed = account.user_type_id.type in ('receivable', 'payable')
#         if is_cash_basis_needed and not self._context.get('move_reverse_cancel'):
#             tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
#             results['tax_cash_basis_moves'] = tax_cash_basis_moves

#         # ==== Check if a full reconcile is needed ====

#         if involved_lines[0].currency_id and all(line.currency_id == involved_lines[0].currency_id for line in involved_lines):
#             is_full_needed = all(line.currency_id.is_zero(line.amount_residual_currency) for line in involved_lines)
#         else:
#             is_full_needed = all(line.company_currency_id.is_zero(line.amount_residual) for line in involved_lines)
#         if is_full_needed:

#             # ==== Create the exchange difference move ====

#             if self._context.get('no_exchange_difference'):
#                 exchange_move = None
#             else:
#                 exchange_move = involved_lines._create_exchange_difference_move()
#                 if exchange_move:
#                     exchange_move_lines = exchange_move.line_ids.filtered(lambda line: line.account_id == account)

#                     # Track newly created lines.
#                     involved_lines += exchange_move_lines

#                     # Track newly created partials.
#                     exchange_diff_partials = exchange_move_lines.matched_debit_ids \
#                                              + exchange_move_lines.matched_credit_ids
#                     involved_partials += exchange_diff_partials
#                     results['partials'] += exchange_diff_partials

#                     exchange_move._post(soft=False)

#             # ==== Create the full reconcile ====

#             results['full_reconcile'] = self.env['account.full.reconcile'].create({
#                 'exchange_move_id': exchange_move and exchange_move.id,
#                 'partial_reconcile_ids': [(6, 0, involved_partials.ids)],
#                 'reconciled_line_ids': [(6, 0, involved_lines.ids)],
#             })

#         # Trigger action for paid invoices
#         not_paid_invoices\
#             .filtered(lambda move: move.payment_state in ('paid', 'in_payment'))\
#             .action_invoice_paid()

#         return results


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pdc_account = fields.Many2one('account.account',string="PDC Account",copy=False)
    custody_account = fields.Many2one('account.account',string="Custody Account",copy=False)

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    # ##############################################################################
    # Pdc part
    pdc_account = fields.Many2one('account.account',string="PDC Account",copy=False)
    custody_account = fields.Many2one('account.account',string="Custody Account",copy=False)
    # state = fields.Selection([('draft','Draft'),('posted','Posted;'),('release', 'Released'), ('cancel','Canceled')])
    pdc_state = fields.Selection(selection=[
            ('draft','Not Relased yet'),
            ('release', 'Released')
            # ('cancel', 'Cancelled'),
        ], string='PDC Status', readonly=True, copy=False, tracking=True,
        default='draft')
    release_move = fields.Many2one(comodel_name='account.move',string='Released Journal Entry',readonly=True, ondelete='cascade',check_company=True,copy=False)
    custody_move = fields.Many2one(comodel_name='account.move',string='Custody Journal Entry',readonly=True, ondelete='cascade',check_company=True,copy=False)
    payment_difference = fields.Monetary(
        compute='_compute_payment_difference')
    # payment_method_code = fields.Char('PAyment Method Code',compute='get_payment_method_code',store=True)
    # payment_difference_handling = fields.Selection([
    #     ('open', 'Keep open'),
    #     ('reconcile', 'Mark as fully paid'),
    # ], default='open', string="Payment Difference Handling")
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", copy=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    writeoff_label = fields.Char(string='Journal Item Label', default='Write-Off',
        help='Change label of the counterpart that will hold the payment difference')
    second_approval_done = fields.Boolean('Second Approval Done',copy=False)
            

    @api.onchange('payment_method_line_id','payment_method_id','payment_method_code')
    def get_joural_pdc_account(self):
        for rec in self:
            if rec.payment_method_code == 'pdc':
                if rec.journal_id.pdc_account:
                    rec.pdc_account = rec.journal_id.pdc_account.id
                else:
                    raise UserError('Assign the PDC account in your journal : %s'%rec.journal_id.name)
            else:
                rec.pdc_account = False

    @api.onchange('payment_method_line_id','payment_method_id','payment_method_code')
    def get_joural_custody_account(self):
        for rec in self:
            if rec.payment_method_code == 'custody':
                if rec.journal_id.custody_account:
                    rec.custody_account = rec.journal_id.custody_account.id
                else:
                    raise UserError('Assign the Custody account in your journal : %s'%rec.journal_id.name)
            else:
                rec.custody_account = False

    @api.depends('amount')
    def _compute_payment_difference(self):
        for payment in self:
            if payment.payment_invoice_ids:
                # if payment.amount > sum(payment.payment_invoice_ids.mapped('reconcile_amount')):
                    
                #     payment.payment_difference = payment.amount - sum(payment.payment_invoice_ids.mapped('reconcile_amount'))
                #     payment.amount_residual = payment.payment_difference
                if payment.amount < sum(payment.payment_invoice_ids.mapped('reconcile_amount')):
                    payment.payment_difference =  sum(payment.payment_invoice_ids.mapped('reconcile_amount')) - payment.amount
                    payment.amount_residual = payment.payment_difference
                else:
                    payment.payment_difference = 0.0
                    payment.amount_residual = payment.payment_difference
            else:
                payment.payment_difference = 0.0
                payment.amount_residual = payment.payment_difference
    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)
    def action_draft(self):
        ''' posted -> draft '''
        self.move_id.button_draft()
        self.release_move.button_draft()
        self.custody_move.button_draft()
        self.write({'pdc_state':'draft','second_approval_done':False})

    def button_open_release_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Released Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.release_move.id,
        }
    
    def button_open_custody_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Custody Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.custody_move.id,
        }

    def release_button(self, write_off_line_vals=None):
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}
        # if self.payment_method_id.code == 'pdc':
            
        # if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
        #     raise UserError(_(
        #         "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
        #         self.journal_id.display_name))

        # Compute amounts.
        write_off_amount = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            counterpart_amount = -self.amount
            write_off_amount *= -1
        elif self.payment_type == 'outbound':
            # Send money.
            counterpart_amount = self.amount
        else:
            counterpart_amount = 0.0
            write_off_amount = 0.0

        balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id,  self.effective_date)
        counterpart_amount_currency = counterpart_amount
        write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.effective_date)
        write_off_amount_currency = write_off_amount
        currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.effective_date,
            partner=self.partner_id,
        )

        if not self.release_move:

            line_vals_list = []
            if self.payment_difference:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.pdc_account.id:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.pdc_account.id,
                        }
                    # else:
                        
                    line_vals_list.append((0,0,vals))
                vals = {
                        'name': 'Relased PDC move %s'%self.name,
                        'date_maturity': self.effective_date,
                        'amount_currency': -counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': self.amount ,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    }
                line_vals_list.append((0,0,vals))
                release_entry = self.env['account.move']
                release_move = release_entry.create({
                        'partner_id': self.partner_id.id,
                        'date': self.effective_date,
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                release_move.action_post()
                self.write({'release_move':release_move.id,'pdc_state':'release'})
            else:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.pdc_account.id:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.pdc_account.id,
                        }
                    else:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': -counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.outstanding_account_id.id,
                        }
                    line_vals_list.append((0,0,vals))
                release_entry = self.env['account.move']
                release_move = release_entry.create({
                        'partner_id': self.partner_id.id,
                        'date': self.effective_date,
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                release_move.action_post()
                self.write({'release_move':release_move.id,'pdc_state':'release'})

        else:
            # for line in self.release_move.line_ids:
            # raise UserError(_(
            #     "Reached Else Condition."))
            self.release_move.line_ids.unlink()

            line_vals_list = []
            if self.payment_difference:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.pdc_account.id:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.pdc_account.id,
                        }
                    # else:
                        
                        line_vals_list.append((0,0,vals))
                vals = {
                        'name': 'Relased PDC move %s'%self.name,
                        'date_maturity': self.effective_date,
                        'amount_currency': -counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': self.amount ,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    }
                line_vals_list.append((0,0,vals))
                # release_entry = self.env['account.move']
                self.release_move.write({
                        'partner_id': self.partner_id.id,
                        'date': self.effective_date,
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        # 'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                self.release_move.action_post()
                self.write({'pdc_state':'release'})
            else:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.pdc_account.id:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.pdc_account.id,
                        }
                    else:
                        vals = {
                            'name': 'Relased PDC move %s'%self.name,
                            'date_maturity': self.effective_date,
                            'amount_currency': -counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.outstanding_account_id.id,
                        }
                    line_vals_list.append((0,0,vals))
                # release_entry = self.env['account.move']
                self.release_move.write({
                        'partner_id': self.partner_id.id,
                        'date': self.effective_date,
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        # 'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                self.release_move.action_post()
                self.write({'pdc_state':'release'})
            # Receivable / Payable.
        #     {
        #         'name': self.payment_reference or default_line_name,
        #         'date_maturity': self.effective_date or self.date,
        #         'amount_currency': counterpart_amount_currency + write_off_amount_currency if currency_id else 0.0,
        #         'currency_id': currency_id,
        #         'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
        #         'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
        #         'partner_id': self.partner_id.id,
        #         'account_id': self.destination_account_id.id,
        #     },
        # ]
        # if write_off_balance:
        #     # Write-off line.
        #     line_vals_list.append({
        #         'name': write_off_line_vals.get('name') or default_line_name,
        #         'amount_currency': -write_off_amount_currency,
        #         'currency_id': currency_id,
        #         'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
        #         'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
        #         'partner_id': self.partner_id.id,
        #         'account_id': write_off_line_vals.get('account_id'),
        #     })

    def second_confirm(self, write_off_line_vals=None):
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}
        # if self.payment_method_id.code == 'pdc':
            
        # if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
        #     raise UserError(_(
        #         "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
        #         self.journal_id.display_name))

        # Compute amounts.
        write_off_amount = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            counterpart_amount = -self.amount
            write_off_amount *= -1
        elif self.payment_type == 'outbound':
            # Send money.
            counterpart_amount = self.amount
        else:
            counterpart_amount = 0.0
            write_off_amount = 0.0

        balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id,  date.today())
        counterpart_amount_currency = counterpart_amount
        write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, date.today())
        write_off_amount_currency = write_off_amount
        currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            date.today(),
            partner=self.partner_id,
        )

        if not self.custody_move:

            line_vals_list = []
            if self.payment_difference:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.custody_account.id:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.custody_account.id,
                        }
                    # else:
                        
                    line_vals_list.append((0,0,vals))
                vals = {
                        'name': 'Custody move %s'%self.name,
                        'date_maturity': date.today(),
                        'amount_currency': -counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': self.amount ,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    }
                line_vals_list.append((0,0,vals))
                release_entry = self.env['account.move']
                custody_move = release_entry.create({
                        'partner_id': self.partner_id.id,
                        'date': date.today(),
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                custody_move.action_post()
                self.write({'custody_move':custody_move.id,'second_approval_done':True})
            else:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.custody_account.id:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.custody_account.id,
                        }
                    else:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': -counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.outstanding_account_id.id,
                        }
                    line_vals_list.append((0,0,vals))
                release_entry = self.env['account.move']
                custody_move = release_entry.create({
                        'partner_id': self.partner_id.id,
                        'date': date.today(),
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                custody_move.action_post()
                self.write({'custody_move':custody_move.id,'second_approval_done':True})

        else:
            # raise UserError(_(
            #     "Reached Else Condition."))
            self.custody_move.line_ids.unlink()

            line_vals_list = []
            if self.payment_difference:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.custody_account.id:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.custody_account.id,
                        }
                    # else:
                        
                        line_vals_list.append((0,0,vals))
                vals = {
                        'name': 'Custody move %s'%self.name,
                        'date_maturity': date.today(),
                        'amount_currency': -counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': self.amount ,
                        'credit': 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    }
                line_vals_list.append((0,0,vals))
                # release_entry = self.env['account.move']
                self.custody_move.write({
                        'partner_id': self.partner_id.id,
                        'date': date.today(),
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        # 'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                self.custody_move.action_post()
                self.write({'second_approval_done':True})
            else:
                for line in self.move_id.line_ids:
                # line_vals_list = [
                    # Liquidity line.
                    if line.account_id.id == self.custody_account.id:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.custody_account.id,
                        }
                    else:
                        vals = {
                            'name': 'Custody move %s'%self.name,
                            'date_maturity': date.today(),
                            'amount_currency': -counterpart_amount_currency,
                            'currency_id': currency_id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'partner_id': self.partner_id.id,
                            'account_id': self.outstanding_account_id.id,
                        }
                    line_vals_list.append((0,0,vals))
                # release_entry = self.env['account.move']
                self.custody_move.write({
                        'partner_id': self.partner_id.id,
                        'date': date.today(),
                        'currency_id': self.currency_id.id,
                        'partner_bank_id': self.partner_bank_id.id,
                        'journal_id': self.journal_id.id,
                        # 'move_type': 'entry',
                        'line_ids': line_vals_list,
                    })
                self.custody_move.action_post()
                self.write({'second_approval_done':True})


    # def write(self,vals):
        
    #     res = super(AccountPayment,self).write(vals)
    #     # raise UserError('Mohon maaf tidak bisa ..')
    #     # for rec in res:
    #     # raise UserError(self.amount_residual)
    #     res['amount_residual'] = self.payment_difference
    #     return res


    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id',
        )):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.

            if writeoff_lines:
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))
                counterpart_amount = counterpart_lines['amount_currency']
                if writeoff_amount > 0.0 and counterpart_amount > 0.0:
                    sign = 1
                else:
                    sign = -1

                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount * sign,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}

            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
            # raise UserError(writeoff_lines)
            if len(line_vals_list) == 3 and not writeoff_lines:
                line_ids_commands = [
                    (1, liquidity_lines.id, line_vals_list[0]),
                    (1, counterpart_lines.id, line_vals_list[1]),
                    (0, 0, line_vals_list[2]),
                ]
            else:
                line_ids_commands = [
                    (1, liquidity_lines.id, line_vals_list[0]),
                    (1, counterpart_lines.id, line_vals_list[1]),
                ]

            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))

            if writeoff_lines:
                line_ids_commands.append((0, 0, line_vals_list[2]))

            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.

            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            })

    # @api.onchange('payment_method_id')
    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}
        if self.payment_method_id.code == 'pdc':

            if not self.outstanding_account_id:
                      raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0

            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else: # payment.payment_type == 'outbound':
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.pdc_account.id,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
        elif self.payment_method_id.code == 'custody':

            if not self.outstanding_account_id:
                      raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0

            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else: # payment.payment_type == 'outbound':
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.custody_account.id,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
        else:
            if not self.outstanding_account_id:
                raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0

            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else: # payment.payment_type == 'outbound':
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
        return line_vals_list

    def _seek_for_lines(self):
        ''' Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        '''
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']


        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:
            if line.account_id in self._get_valid_liquidity_accounts():
                liquidity_lines += line
            elif line.account_id.internal_type in ('receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                counterpart_lines += line
            else:
                writeoff_lines += line

        return liquidity_lines, counterpart_lines, writeoff_lines

    def _get_valid_liquidity_accounts(self):
        return (
            self.journal_id.default_account_id,
            self.payment_method_line_id.payment_account_id,
            self.journal_id.company_id.account_journal_payment_debit_account_id,
            self.journal_id.company_id.account_journal_payment_credit_account_id,
            self.journal_id.inbound_payment_method_line_ids.payment_account_id,
            self.journal_id.outbound_payment_method_line_ids.payment_account_id,
            self.journal_id.pdc_account,
            self.journal_id.custody_account,
        )

    # def _synchronize_from_moves(self, changed_fields):
    #     ''' Update the account.payment regarding its related account.move.
    #     Also, check both models are still consistent.
    #     :param changed_fields: A set containing all modified fields on account.move.
    #     '''
    #     if self._context.get('skip_account_move_synchronization'):
    #         return

    #     for pay in self.with_context(skip_account_move_synchronization=True):

    #         # After the migration to 14.0, the journal entry could be shared between the account.payment and the
    #         # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
    #         if pay.move_id.statement_line_id:
    #             continue

    #         move = pay.move_id
    #         move_vals_to_write = {}
    #         payment_vals_to_write = {}

    #         if 'journal_id' in changed_fields:
    #             if pay.journal_id.type not in ('bank', 'cash'):
    #                 raise UserError(_("A payment must always belongs to a bank or cash journal."))

    #         if 'line_ids' in changed_fields:
    #             all_lines = move.line_ids
    #             liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

    #             # if len(liquidity_lines) != 1 or len(counterpart_lines) != 1:
    #             #     raise UserError(_(
    #             #         "The journal entry %s reached an invalid state relative to its payment.\n"
    #             #         "To be consistent, the journal entry must always contains:\n"
    #             #         "- one journal item involving the outstanding payment/receipts account.\n"
    #             #         "- one journal item involving a receivable/payable account.\n"
    #             #         "- optional journal items, all sharing the same account.\n\n"
    #             #     ) % move.display_name)

    #             # if writeoff_lines and len(writeoff_lines.account_id) != 1:
    #             #     raise UserError(_(
    #             #         "The journal entry %s reached an invalid state relative to its payment.\n"
    #             #         "To be consistent, all the write-off journal items must share the same account."
    #             #     ) % move.display_name)

    #             # if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
    #             #     raise UserError(_(
    #             #         "The journal entry %s reached an invalid state relative to its payment.\n"
    #             #         "To be consistent, the journal items must share the same currency."
    #             #     ) % move.display_name)

    #             # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
    #             #     raise UserError(_(
    #             #         "The journal entry %s reached an invalid state relative to its payment.\n"
    #             #         "To be consistent, the journal items must share the same partner."
    #             #     ) % move.display_name)

    #             if counterpart_lines.account_id.user_type_id.type == 'receivable':
    #                 partner_type = 'customer'
    #             else:
    #                 partner_type = 'supplier'

    #             liquidity_amount = liquidity_lines.amount_currency

    #             move_vals_to_write.update({
    #                 'currency_id': liquidity_lines.currency_id.id,
    #                 'partner_id': liquidity_lines.partner_id.id,
    #             })
    #             payment_vals_to_write.update({
    #                 'amount': abs(liquidity_amount),
    #                 'payment_type': 'inbound' if liquidity_amount > 0.0 else 'outbound',
    #                 'partner_type': partner_type,
    #                 'currency_id': liquidity_lines.currency_id.id,
    #                 'destination_account_id': counterpart_lines.account_id.id,
    #                 'partner_id': liquidity_lines.partner_id.id,
    #             })

    #         move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
    #         pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))


     # ##############################################################################

class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model_create_multi
    def create(self, vals_list):
        payment_methods = super(models.Model,self).create(vals_list)
        methods_info = self._get_payment_method_information()
        for method in payment_methods:
            information = methods_info.get(method.code)
            if information:
                if information.get('mode') == 'multi':
                    method_domain = method._get_payment_method_domain()

                    journals = self.env['account.journal'].search(method_domain)

                    self.env['account.payment.method.line'].create([{
                        'name': method.name,
                        'payment_method_id': method.id,
                        'journal_id': journal.id
                    } for journal in journals])
            else:
                if method.code == 'pdc':
                    journals = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))])

                    self.env['account.payment.method.line'].create([{
                        'name': method.name,
                        'payment_method_id': method.id,
                        'journal_id': journal.id
                    } for journal in journals])
                elif method.code == 'custody':
                    journals = self.env['account.journal'].search([('type', '=', 'cash')])

                    # raise UserError('Mohon maaf tidak bisa ..')
                    if journals:
                        self.env['account.payment.method.line'].create([{
                            'name': method.name,
                            'payment_method_id': method.id,
                            'journal_id': journal.id
                        } for journal in journals])
        return payment_methods