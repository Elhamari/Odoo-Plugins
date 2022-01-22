# -*- coding: utf-8 -*-
{
    'name': 'AppsGate HR Loan Management',
    'version': '15.0.1.0.0',
    'summary': 'Manage Loan Requests',
    'description': """
        -Helps you to manage Loan Requests of your company's staff.
        -Helps you to manage Advance Salary Request of your company's staff.
        """,
    'category': 'Human Resources',
    'author': "AppsGate",
    'depends': [
        'base', 'hr_payroll', 'hr', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
        'views/hr_loan_config.xml',
        #'views/salary_structure.xml',
        'views/salary_advance.xml',

    ],
    'images': ['static/description/banner.png'],
    'license': 'OEEL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
}
