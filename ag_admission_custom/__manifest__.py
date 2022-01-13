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
    'depends': ['base','openeducat_admission'],
    'data': [


        'security/ir.model.access.csv',
        # 'security/hr_security.xml',
        # 'views/report.xml',
        'views/admission.xml',

        # 'views/self_service.xml',
        'data/sequence.xml',

        # 'views/print_certificate.xml',

    ],
    'images': [
        'static/src/img/main-screenshot.png'
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
