from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta , date

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)
    cheque_state = fields.Selection(selection=[
            ('deposit', 'DEPOSITED'),
            ('return', 'RETURNED'),
            ('cancel', 'CANCELLED'),
            ('bounce', 'BOUNCED'),
        ], string='Status', readonly=True, copy=False, tracking=True)
    bounce_move = fields.Many2one(comodel_name='account.move',string='Bounced Journal Entry',readonly=True, ondelete='cascade',check_company=True)
    cheque_count = fields.Integer(compute='_cheque_count', string='# Cheque')

    def _cheque_count(self):
        for each in self:
            cheque_ids = self.env['account.move'].search([('cheque_payment_id', '=', each.id)])
            each.cheque_count = len(cheque_ids)
    



    def cheque_entry_view(self):
        for each1 in self:
            move_obj = self.env['account.move'].search([('cheque_payment_id', '=', each1.id)])
            move_ids = []
            for each in move_obj:
                move_ids.append(each.id)
            view_id = self.env.ref('account.view_move_form').id
            if move_ids:
                if len(move_ids) <= 1:
                    value = {
                        'view_mode': 'form',
                        'res_model': 'account.move',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Account Entries'),
                        'res_id': move_ids and move_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', move_ids)]),
                        'view_mode': 'tree',
                        'res_model': 'account.move',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Account Entries'),
                        'res_id': move_ids
                    }

                return value

        
    def action_post(self):
        ''' draft -> posted '''
        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
        self.cheque_state = 'deposit'
        
    def deposite_cheque(self):
        line_vals_list = []
        vals_deb = {
            'name': 'Deposite PDC No.%s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': self.amount,
            'currency_id': self.currency_id.id,
            'debit': self.amount,
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.outstanding_account_id.id,
        }
        line_vals_list.append((0,0,vals_deb))

        vals_crd = {
            'name': 'Deposite PDC No.%s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': -self.amount,
            'currency_id': self.currency_id.id,
            'debit': 0.0,
            'credit': self.amount,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.journal_id.bounce_account.id,
            }
        line_vals_list.append((0,0,vals_crd))
        release_entry = self.env['account.move']
        release_move = release_entry.create({
            'name':'Deposite PDC No.%s'%self.cheque_reference,
            'partner_id': self.partner_id.id,
            'date': self.date.today(),
            'currency_id': self.currency_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'cheque_payment_id': self.id,
            'line_ids': line_vals_list,
            })
        release_move.action_post()
        self.write({'cheque_state':'deposit'})


        
    def return_cheque(self):
        line_vals_list = []
        vals_deb = {
            'name': 'Return PDC No.%s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': self.amount,
            'currency_id': self.currency_id.id,
            'debit': self.amount,
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.partner_id.property_account_receivable_id.id,
        }
        line_vals_list.append((0,0,vals_deb))

        vals_crd = {
            'name': 'Return PDC No.%s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': -self.amount,
            'currency_id': self.currency_id.id,
            'debit': 0.0,
            'credit': self.amount,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.journal_id.bounce_account.id,
            }
        line_vals_list.append((0,0,vals_crd))
        release_entry = self.env['account.move']
        release_move = release_entry.create({
            'name':'Return PDC No.%s'%self.cheque_reference,
            'partner_id': self.partner_id.id,
            'date': self.date.today(),
            'currency_id': self.currency_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'cheque_payment_id': self.id,
            'line_ids': line_vals_list,
            })
        release_move.action_post()
        self.write({'cheque_state':'return'})     
        

         




    def bounce_check(self):
        line_vals_list = []
        vals_deb = {
            'name': 'Bounced PDC No.%s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': self.amount,
            'currency_id': self.currency_id.id,
            'debit': self.amount,
            'credit': 0.0,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.journal_id.bounce_account.id,
        }
        line_vals_list.append((0,0,vals_deb))

        vals_crd = {
            'name': 'Bounced PDC No. %s'%self.cheque_reference,
            'date_maturity': self.date.today(),
            'amount_currency': -self.amount,
            'currency_id': self.currency_id.id,
            'debit': 0.0,
            'credit': self.amount,
            'partner_id': self.partner_id.id,
            #'cheque_payment_id': self.id,
            'account_id': self.outstanding_account_id.id,
            }
        line_vals_list.append((0,0,vals_crd))
        release_entry = self.env['account.move']
        release_move = release_entry.create({
            'name':'Bounced PDC No.%s'%self.cheque_reference,
            'partner_id': self.partner_id.id,
            'date': self.date.today(),
            'currency_id': self.currency_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'journal_id': self.journal_id.id,
            'move_type': 'entry',
            'cheque_payment_id': self.id,
            'line_ids': line_vals_list,
            })
        release_move.action_post()
        self.write({'cheque_state':'bounce'})
  


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bounce_account = fields.Many2one('account.account',string="Bounce Account",copy=False)
    box_account = fields.Many2one('account.account',string="Box Account",copy=False)    
    
    
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
        return payment_methods


class AccountMove(models.Model):
    _inherit = 'account.move'

    cheque_payment_id = fields.Many2one('account.payment',string="Cheque Payment",copy=False)
   
    