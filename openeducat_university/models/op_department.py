# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright(C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

from odoo import models, fields, api, _


class OpDepartment(models.Model):
    _inherit = "op.department"

    company_id = fields.Many2one(
        'res.company', string='Company')

    course_count = fields.Integer(
        compute="_compute_course_data", string='Course Count')

    course = fields.Char(string="Course", default='Course')
    department = fields.Char('Department', default='Department')

    child_department_count = fields.Integer(
        compute="_compute_child_department_count_data", string='Child Department')

    @api.onchange('company_id')
    def _onchange_course(self):
        for data in self:
            data.course = data.company_id.course

    def _compute_course_data(self):
        for course in self:
            course_list = self.env['op.course'].search_count(
                [('department_id', 'in', [course.id])])
            course.course_count = course_list

    def _compute_child_department_count_data(self):
        for department in self:
            if department.company_id:
                child_department_list = self.env['op.department'].search_count(
                    [('parent_id', 'in', [department.id])])
                # print("-----child-----aaa-----", child_department_list)
                department.child_department_count = child_department_list


class OpSection(models.Model):
    _inherit = "op.section"

    department_id = fields.Many2one('op.department', string='Department')
