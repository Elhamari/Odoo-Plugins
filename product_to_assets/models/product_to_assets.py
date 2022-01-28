from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductToAssets(models.Model):
    _name = "product.to.assets"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    # sequence
    @api.model
    def create(self, vals):
        res = super(ProductToAssets, self).create(vals)
        next_seq = self.env['ir.sequence'].get('product.to.assets.sequence')
        res.update({'name': next_seq})
        return res

    READONLY_STATES = {
        'approve': [('readonly', True)],
        'confirmed': [('readonly', True)],
        'close': [('readonly', True)],
    }
    name = fields.Char("Name")

    date_order = fields.Datetime('Date', required=True, index=True,
                                 default=fields.Datetime.now,
                                 states={'close': [('readonly', True)], 'confirmed': [('readonly', True)],
                                         'approve': [('readonly', True)]}, copy=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('close', 'Closed')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    note = fields.Text(string='Note')
    order_line = fields.One2many('assets.order.line', 'order_id', string='Assets Lines',
                                 states={'close': [('readonly', True)], 'confirmed': [('readonly', True)],
                                         'approve': [('readonly', True)]}, copy=True)
    picking_ids = fields.Many2many('stock.picking', string='Picking ', copy=False, store=True)
    assets_ids = fields.Many2many('account.asset', string='Assets', copy=False, store=True)
    move_id = fields.Many2many('account.move', string='Move', copy=False, store=True)

    def action_view_move(self):
        for rec in self:
            return {
                'name': 'Movw',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', rec.move_id.ids)],

            }

    def action_view_assets(self):
        for rec in self:
            return {
                'name': 'Assets',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.asset',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', rec.assets_ids.ids)],

            }

    def action_view_picking(self):

        for rec in self:
            return {
                'name': 'Delivery Orders',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', rec.picking_ids.id)],

            }

    def to_approve(self):
        for rec in self:
            rec.state = 'approve'

    def to_confirmed(self):
        for rec in self:
            type = self.env['stock.picking.type'].search([('sequence_code', '=', 'OUT')])
            location = self.env['stock.warehouse'].search([('partner_id', '=', self.env.user.company_id.partner_id.id)])
            opreation = self.env['stock.location'].search(
                [('warehouse_id', '=', location.id), ('usage', '=', 'internal')], limit=1)
            dest_opreation = self.env['stock.location'].search([('usage', '=', 'customer')])
            stock_picking_vals = {'partner_id': self.env.user.company_id.partner_id.id,
                                  'location_dest_id': dest_opreation.id,
                                  'scheduled_date': rec.date_order,
                                  'picking_type_id': type.id,
                                  'location_id': opreation.id,
                                  'origin': rec.name,
                                  }
            picking_id = self.env['stock.picking'].create(stock_picking_vals)
            Assest_ids = []
            moves_ids = []
            for line in self.order_line:
                src_loc_id = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id), ('quantity', '>', 0)], limit=1)
                src_loc = src_loc_id.location_id

                stock_move_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'quantity_done': line.product_qty,
                    'product_uom': line.product_id.product_tmpl_id.uom_id.id,
                    'location_id': src_loc.id,
                    'name': line.product_id.name,
                    'location_dest_id': dest_opreation.id,
                    'picking_id': picking_id.id,
                    'warehouse_id': location.id,
                    'company_id': self.env.company.id,
                    'state': 'draft',
                }
                count = line.product_qty

                journal_id = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
                while count >= 1:
                    assets_vals = {
                        'name': line.product_id.name,
                        # 'category_id': line.category_id.id,
                        'account_asset_id': line.account_id.id,
                        'account_depreciation_id': line.account_id.id,
                        'account_depreciation_expense_id': line.product_id.categ_id.property_account_expense_categ_id.id,
                        'journal_id': journal_id.id,
                        'acquisition_date': rec.date_order,
                        'asset_type': 'purchase',
                        'original_value': line.product_id.standard_price,
                    }
                    assets = self.env['account.asset'].create(assets_vals)
                    Assest_ids.append(assets.id)
                    rec.assets_ids = Assest_ids
                    # assets.validate()

                    count = count - 1
                move = self.env['stock.move'].create(stock_move_vals)
                 # adding account move
                debit_line_vals = {
                    'name': line.product_id.name,
                    'debit': line.product_id.standard_price * line.product_qty,
                    'credit': 0.0,
                    'account_id': line.account_id.id,
                }
                credit_line_vals = {
                    'name': line.product_id.name,
                    'debit': 0.0,
                    'credit': line.product_id.standard_price * line.product_qty,
                    'account_id': line.product_id.categ_id.property_stock_account_output_categ_id.id,
                }
                line_ids = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
                move_vals = {
                    'date': rec.date_order,
                    'journal_id': journal_id.id,
                    'line_ids': line_ids,
                }
                print("move_vals", move_vals)
                journal_ent = self.env['account.move'].create(move_vals)
                moves_ids.append(journal_ent.id)
                rec.move_id = moves_ids

            rec.state = 'confirmed'

            rec.picking_ids = [picking_id.id]
            picking_id.button_validate()

    def to_close(self):
        for rec in self:
            rec.state = 'close'


class AssetsOrderLine(models.Model):
    _name = 'assets.order.line'
    _description = 'Assets Order Line'

    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 change_default=True, required=True, )
    # category_id = fields.Many2one("account.asset.category", string="Asset Category", required=True)
    order_id = fields.Many2one('product.to.assets', string='Assets Reference', index=True, required=True,
                               ondelete='cascade')
    account_id = fields.Many2one('account.account', store=True, string='Assets Account', readonly=False, required=True)

    state = fields.Selection(related='order_id.state', store=True)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    assets_ok = fields.Boolean('Can Be Assets', default=False)
