# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

from odoo import models, fields, api, _


class OpStudent(models.Model):
    _inherit = "op.student"

    cast_category_id = fields.Many2one('op.cast.category', string="Cast Category")
    casts_id = fields.Many2one('op.casts', string="Casts")
    mother_tongue_id = fields.Many2one('mother.tongue.lang', string="Mother Tongue")
    religion_id = fields.Many2one('op.religion', string="Religion")
