# -*- coding: utf-8 -*-
#############################################################################
#
#    # Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY # Technologies(<https://www.#.com>).
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': "Payroll Transactions salary Extend",
    'version': '14.0',
    'category': "Generic Modules/Human Resources",
    'summary': """Payroll Transactions""",
    'description': """

            Employee user
    """,
    'author': 'APPSGATE FZC LLC',
    'company': 'APPSGATE FZC LLC',
    'depends': ['base', 'hr', 'hr_payroll','hr_contract','l10n_ae_hr_payroll'],
    'data': [

        'security/ir.model.access.csv',
        #'data/payroll_data.xml',
        'views/hr_contract.xml'

    ],
    'images': [
        'static/src/img/main-screenshot.png'
    ],

    # 'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'currency': 'USD',
    'price': 20.00,
}
