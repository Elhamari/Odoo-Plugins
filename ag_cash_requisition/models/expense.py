# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
import math
import time
from odoo.exceptions import UserError, AccessError, ValidationError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    cash_req_id = fields.Many2one('cash.requisition', string='Petty Cash')