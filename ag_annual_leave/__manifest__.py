# -*- coding: utf-8 -*-

# Part of Sananaz Mansuri See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Annual Leaves',
    'version': '14.0',

    'summary': """""",
    'description': """




    """,
    'author': 'APPSGATE FZC LLC',
    'website': 'http://www.odoo.com',
    'category': 'Human Resources',
    'depends': [
        'hr',
        'hr_holidays','hr_payroll','hr_employee_updation'
    ],
    'data': [
        'data/leave_data.xml',

        'views/employee.xml',
        'views/hr_holiday.xml',
        'views/hr_leave.xml'
    ],
    'installable': True,
    'application': False,

    'assets': {
        'web.assets_backend': [
            'hr_leave_request_aliasing/static/src/**/*',
        ],
    }
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: