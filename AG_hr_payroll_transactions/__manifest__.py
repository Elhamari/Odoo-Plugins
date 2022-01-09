# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Payroll Transactions',
    'version': '12.0.1',
    'category': 'Human Resources Module',
    'author': 'APPSGATE FZC LLC',
    'Category':'HR',
    'website':'https://apps-gate.net',
    'description': """
    This Module allows you to manage all type of expenses
    """,
    'depends': [
        'hr','hr_payroll','base','hr_timesheet'

    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll.xml',
        #'views/hr_recuirtment.xml'
    ],

    'images':[
        'static/src/img/main-screenshot.png'
    ],

    'license': 'AGPL-3',
    'installable': True,
    'price':'10',
    'currency':'USD',
    'auto_install': False,
    'application': True,
}
