# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################
from odoo import models, fields, api


class MotherTongueLang(models.Model):
    _name = "mother.tongue.lang"
    _description = "Mother Tongue Language"

    name = fields.Char(string='Name', required=True)
