# -*- coding: utf-8 -*-

{
    'name': 'Final Settlement & Gratuity',
    'version': '12.0',
    'category': 'HR',
    'summary': 'HR Management',
    'description': """
                    final settlement,
                    gratuity,
                    """,
    'author': 'APPSGATE FZC LLC',
    'website': 'http://www.apps-gate.net',

    'images':[
        'static/src/img/main-screenshot.png'
    ],

    'depends': ['base', 'hr_payroll', 'hr_contract','hr_holidays'],
    'data': [
                'security/ir.model.access.csv',
                'data/data.xml',
                'views/final_settlement_view.xml',
                'views/final_settlement_type_master.xml',
                'wizard/refuse_reason.xml',
                'report/settlement_report.xml',
                'report/report_menu.xml'
    
    ],
    'price':'20',
    'currency':'USD',
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
