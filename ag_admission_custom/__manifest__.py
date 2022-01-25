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
    'name': "Admission Customization",
    'version': '15.0',
    'category': "Education",
    'summary': """Additional Customization on the admission process""",
    # 'description':"""
    
    #         Complete Employee Self Service'
    #               'certicate',
    #               'letter',
    #               'letters',
    #               'certificates',
    #               'salary certificate',
    #               'experience certificate',
    #               'NOC',
    #               'self service',
    #               'employee',
    #               'ESS'
    # """,
    'author': 'APPSGATE FZC LLC',
    'company': 'APPSGATE FZC LLC',
    'depends': ['base','openeducat_admission','openeducat_online_admission','openeducat_admission_enterprise','openeducat_core_enterprise','openeducat_cbcs'],
    'data': [


        'security/ir.model.access.csv',
        # 'security/hr_security.xml',
        # 'views/report.xml',
        'views/admission.xml',
        'views/admission_website.xml',
        'views/courses.xml',
        'views/subject_regestration_view.xml',

        # 'views/self_service.xml',
        'data/sequence.xml',

        # 'views/print_certificate.xml',

    ],
    'images': [
        'static/src/img/main-screenshot.png'
    ],
    'assets': {
        'web._assets_primary_variables': [
            # 'account/static/src/scss/variables.scss',
        ],
        'web.assets_backend': [
            # 'ag_admission_custom/static/src/css/class.css',
            
        ],
        'web.assets_frontend': [
            # 'account/static/src/js/account_portal_sidebar.js',
            'ag_admission_custom/static/src/js/map.js',
            '/ag_admission_custom/static/src/js/selectionn.js',
        ],
        'web.assets_tests': [
            # 'account/static/tests/tours/**/*',
        ],
        'web.qunit_suite_tests': [
            # ('after', 'web/static/tests/legacy/views/kanban_tests.js', 'account/static/tests/account_payment_field_tests.js'),
            # ('after', 'web/static/tests/legacy/views/kanban_tests.js', 'account/static/tests/section_and_note_tests.js'),
        ],
        'web.assets_qweb': [
            # 'account/static/src/xml/**/*',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,
}
