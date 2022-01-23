# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################
from odoo import models, fields, api, _


class OpCastCategory(models.Model):
    _name = "op.cast.category"
    _description = "Cast Category"

    name = fields.Char("Name", required=True)
