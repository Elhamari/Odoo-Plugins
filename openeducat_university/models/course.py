# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################


from odoo import models, fields, api


class OpBatch(models.Model):
    _inherit = "op.course"

    batch = fields.Char()
    trainee = fields.Char()

    @api.onchange('company_id')
    def _onchange_data(self):
        for rec in self:
            rec.batch = rec.company_id.batch
            rec.trainee = rec.company_id.trainee
