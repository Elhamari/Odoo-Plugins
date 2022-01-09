# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payslip Leave Calculation',
    'version': '14.0',
    'category': 'Payslip',
    'summary': 'UAE leaves and payroll',

    'description': """


""",

    'author': 'APPSGATE FZC LLC',
    # 'website': 'http://www.browseinfo.in',
    'images': [],
    'depends': ['base', 'hr_holidays','hr_payroll','hr_vacation_mngmt','hr','hr_timesheet'],
    'data': [
       # 'security/ir.model.access.csv',
        'views/payslip.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    # 'live_test_url' : 'https://youtu.be/bp7QLc_zEAg',
    # "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
