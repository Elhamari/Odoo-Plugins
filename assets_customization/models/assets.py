from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssetsToSale(models.TransientModel):
    _inherit = "account.asset.sell"

    customer_id = fields.Many2one('res.partner', 'Customer Name')
    currency_id = fields.Many2one('res.currency', readonly=True)
    sale_price = fields.Monetary(currency_field='currency_id', string='Sale Price')

    def do_action(self):
        self.ensure_one()
        if self.action == 'sell':
            print("sell")
            journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            invoice_vals = {'partner_id': self.customer_id.id,
                            'invoice_date': fields.Date.today(),
                            'move_type': 'out_invoice',
                            'journal_id': journal_id.id,
                            'invoice_line_ids': [
                                (0, 0, {'name': self.asset_id.name, 'quantity': 1, 'price_unit': self.sale_price, })]
                            }
            print("invoice_vals", invoice_vals)
            invoice_id = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice_id.id
            self.asset_id.invoice_id = invoice_id.id
            print("invoice_move_vals", invoice_id)
            invoice_line = invoice_id.invoice_line_ids
            return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)
        else:
            invoice_line = self.env[
                'account.move.line'] if self.action == 'dispose' else self.invoice_line_id or self.invoice_id.invoice_line_ids
            return self.asset_id.set_to_close(invoice_line_id=invoice_line, date=invoice_line.move_id.invoice_date)


class AccountAsset(models.Model):
    _inherit = "account.asset"
    invoice_id = fields.Many2one('account.move', string="Sold Invoice")

    def action_view_invoice(self):
        for rec in self:
            return {
                'name': 'Sold Asset',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', self.invoice_id.id)],

            }
