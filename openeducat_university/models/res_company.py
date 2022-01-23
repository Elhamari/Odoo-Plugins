# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################


from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    child_count = fields.Integer(compute='_compute_child_count_data')
    department_count = fields.Integer(compute='_compute_department_count_data', string="Academic Branch")
    label_company = fields.Char(string='Use Campus as', default='Campus')
    color = fields.Integer(string='Color Index', default=0)

    batch = fields.Char(string='Use Batch as', default='Batch')
    course = fields.Char(string='Use Course as', default='Course')
    label_department = fields.Char(string='Use Department as', default='Academic Branch')
    trainee = fields.Char(string='Use Student as', default='Student')

    def _compute_child_count_data(self):
        for record in self:
            child_list = self.env['res.company'].search_count([('parent_id', 'in', [record.id])])
            record.child_count = child_list

    def _compute_department_count_data(self):
        for record in self:
            if not record.parent_id:
                department_list = self.env['op.department'].search_count(
                    [('company_id', 'in', [record.id])])
                # print("==iiiiii======", department_list)
                record.department_count = department_list
            elif record.parent_id:
                department_list = self.env['op.department'].search_count(
                    [('parent_id', '=', False), ('company_id', 'in', [record.id])])
                record.department_count = department_list

            # else:
            #     if record.parent_id:
            #         department_list = self.env['op.department'].search_count(
            #             [('parent_id', 'in', True), ('company_id', 'in', [record.id])])
            #         record.department_count = department_list
            # else:
            #     if list.parent_id:
            #         record.department_count = department_list
