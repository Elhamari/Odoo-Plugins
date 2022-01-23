# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################
from odoo import models, fields, api, _


class OpReligion(models.Model):
    _name = "op.religion"
    _description = "Religion"

    name = fields.Char("Religion Name", required=True)
