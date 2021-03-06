from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta , date

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    custody_account = fields.Many2one('account.account',string="Custody Account",copy=False)
  
    custody_state = fields.Selection(selection=[
            ('draft', 'Employee Custody'),
            ('deposit', 'Main Treasury'),
        ], string='Status', readonly=True, copy=False, tracking=True)
  
    custody_move = fields.Many2one(comodel_name='account.move',string='Custody Journal Entry',readonly=True, ondelete='cascade',check_company=True,copy=False)
    payment_difference = fields.Monetary(
        compute='_compute_payment_difference')
        
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", copy=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    writeoff_label = fields.Char(string='Journal Item Label', default='Write-Off',
        help='Change label of the counterpart that will hold the payment difference')
    second_approval_done = fields.Boolean('Second Approval Done',copy=False)
    custody_date = fields.Date('Date', copy=False, default=fields.Date.today)        

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
                



        
    def action_post(self):
        ''' draft -> posted '''
        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
        self.custody_state = 'draft'
        

    def second_confirm(self, write_off_line_vals=None):
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

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
                self.write({'custody_move':custody_move.id,'second_approval_done':True, 'custody_state': 'deposit'})
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
                self.write({'custody_move':custody_move.id,'second_approval_done':True, 'custody_state': 'deposit'})

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
                self.write({'second_approval_done':True, 'custody_state': 'deposit'})
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
                self.write({'second_approval_done':True, 'custody_state': 'deposit'})


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
        
        

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    custody_account = fields.Many2one('account.account',string="Custody Account",copy=False)    
    
 


class AccountMove(models.Model):
    _inherit = 'account.move'

    custody_payment_id = fields.Many2one('account.payment',string="Cheque Payment",copy=False)
   
    
