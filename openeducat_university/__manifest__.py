# -*- coding: utf-8 -*-
# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.
#
##############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech Receptives(<http://www.techreceptives.com>).
#
##############################################################################

{
    'name': "OpenEduCat University",
    'version': '15.0',
    'category': 'Education',
    'sequence': 3,
    'summary': "Manage University""",
    'complexity': "easy",
    'author': 'Tech Receptives',
    'website': 'http://www.openeducat.org',
    'depends': [
        'openeducat_core_enterprise',
    ],
    'data': ['security/ir.model.access.csv',
             'views/course_desboard_view.xml',
             'views/department_view.xml',
             'views/res_company_view.xml',
             'views/course_category_view.xml',
             'views/cast_category_view.xml',
             'views/op_casts_view.xml',
             'views/mother_tongue.xml',
             'views/religion_view.xml',
             'views/student_view.xml',
             'menu/university_menu.xml',
             ],
    'demo': [
        'demo/company_demo.xml',
        'demo/op_department.xml',
        'demo/cast_category_demo.xml',
        'demo/casts_demo.xml',
        'demo/religion_demo.xml',
        'demo/mother_tongue_demo.xml',
    ],
    'css': [],
    'qweb': [],
    'js': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 75,
    'currency': 'EUR',
    'license': 'OPL-1',
    'live_test_url': 'https://www.openeducat.org/plans'
}
