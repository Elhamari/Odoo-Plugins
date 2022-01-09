# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    # Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY # Technologies (<https://www.#.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Open HRMS Reminders Todo',
    'version': '14.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'summary': 'HR Reminder For OHRMS',
    'author': 'APPSGATE FZC LLC',
    'company': 'APPSGATE FZC LLC',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_reminder_security.xml',
        'views/hr_reminder_view.xml',
       # 'views/reminder_template.xml',
    ],

    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

    'assets': {

        'web.assets_backend': [
            'hr_reminder/static/src/css/notification.css',

        ],
        'web.qunit_suite_tests': [
            'hr/static/tests/helpers/mock_models.js',
            'hr/static/tests/m2x_avatar_employee_tests.js',
            'hr/static/tests/standalone_m2o_avatar_employee_tests.js',
        ],
        'web.assets_qweb': [
            'hr_reminder/static/src/xml/reminder_topbar.xml',
        ],
    },


}
