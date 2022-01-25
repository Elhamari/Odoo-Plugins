# Part of OpenEduCat. See LICENSE file for full copyright & licensing details.
#
##############################################################################
#
#    OpenEduCat Inc.
#    Copyright (C) 2009-TODAY OpenEduCat Inc(<http://www.openeducat.org>).
#
##############################################################################

# from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import http, _
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
import dateutil.parser
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.website.controllers.main import QueryURL
from odoo.osv import expression
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from markupsafe import Markup
import base64
import base64
import calendar
from datetime import datetime, date

from odoo.http import request, Response
from odoo.addons.website.controllers.main import QueryURL

from odoo import fields
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv import expression
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.exceptions import UserError
from odoo.addons.portal.controllers.portal import CustomerPortal


class AdmissionRegistration(http.Controller):

    @http.route(['/admissionregistration'], type='http',
                auth='public', website=True)
    def admission_registration(self, **post):
        register_ids = request.env['op.admission.register'].sudo().search(
            [('state', '=', 'application')])
        country_ids = request.env['res.country'].sudo().search([])
        certificate_types = request.env['certificate.type'].sudo().search([])
        institute_types = request.env['institute.type'].sudo().search([])
        student_id = request.env['op.student'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id)])
        post.update({
            'register_ids': register_ids,
            'countries': country_ids,
            'certificate_types': certificate_types,
            'institute_types': institute_types,
            'student_id': student_id,
            'partner_id': request.env.user.partner_id,
        })
        return request.render(
            "openeducat_online_admission.admission_registration", post)


    @http.route(['/get/application_data'],
                type='json', auth="none", website=True)
    def get_application_data(self, application, **kw):

        student_id = request.env['op.student'].sudo().search_read(
            domain=[('partner_id', '=', int(application))],
            fields=['first_name', 'middle_name', 'last_name',
                    'gender', 'email', 'mobile', 'phone', 'street', 'city',
                    'zip', 'country_id', 'birth_date', 'partner_id', 'user_id','passport_number','passport_country_issue','passport_issued_date','passport_end_date','eid_number','uid','eid_end_date','residency_number','residency_state','residency_issued_date','residency_end_date','school_name','score','certificate_origin','sec_issued_date','sec_state','school_system','institute_type','certificate_type','personal_photo','cert_of_good_conduct','medical_check','passport_photo','birthday_cert','pledge'])
                    # 

        country_id = request.env['res.country'].sudo().search_read(domain=[],
                                                                   fields=['name'])

        if application != '0':
            return {'student_id': student_id,
                    'country_id': country_id}
        else:
            return {'country': country_id}

class WebsiteSale(WebsiteSale):

    @http.route()
    def confirm_order(self, **post):
        val = post.copy()
        admission_id = False
        if val and val.get('register_id', False):
            register = request.env['op.admission.register'].sudo().search(
                [('id', '=', int(val['register_id']))])
            product_id = register.product_id
            lst_price = register.product_id.lst_price
            val.update({'register_id': register.id,
                        'course_id': register.course_id.id,
                        'application_date': datetime.today(),
                        'fees': product_id and lst_price or 0.0,
                        'name': post.get('first_name') + ' ' + post.get(
                            'middle_name') + ' ' + post.get('last_name'),
                        'fees_term_id': register.course_id.fees_term_id.id,
                        'student_id': post.get('student_id'),
                        'company_id': register.company_id.id,
                        'state': 'online'})
            attach2 = False
            attach3 = False
            if post.get('personal_photo',False):
                attach = request.httprequest.files.getlist('personal_photo')
                for attachment in attach:
                    # file = post.get('attachment')
                    attachment = attachment.read()
                    val['personal_photo'] = base64.b64encode(attachment.read())
                    val['cert_of_good_conduct'] = base64.encodestring(val['cert_of_good_conduct'])

            attached_files = attach2
            attached_files2 = val['cert_of_good_conduct']
            attached_files3 = val['medical_check']
            attached_files4 = val['passport_photo']
            attached_files5 = val['birthday_cert']
            # attach2 = False
            # for attachment in attach:
            #     attached_file = attachment.read()
            #     attach2 = base64.encodestring(attached_file)
            attached_files6 = val['pledge']
            if val['personal_photo']:
                
                val['personal_photo_bol'] = True
                # val['personal_photo'] = False
            if val['cert_of_good_conduct']:
                val['cert_of_good_conduct_bol'] = True
                # val['cert_of_good_conduct'] = False
            if val['medical_check']:
                val['medical_check_bol'] = True
                val['medical_check'] = False
            if val['passport_photo']:
                val['passport_photo_bol'] = True
                val['passport_photo'] = False
            if val['birthday_cert']:
                val['birthday_cert_bol'] = True
                val['birthday_cert'] = False
            if val['pledge']:
                val['pledge_bol'] = True
                val['pledge'] = False
            # if post.get('personal_photo',False):
            #     val['personal_photo_bol'] = True
            #     attached_files = request.httprequest.files.getlist('personal_photo')
            #     for attachment in attached_files:
            #         val['personal_photo'] = attachment.read()
            # if post.get('cert_of_good_conduct',False):
            #     val['cert_of_good_conduct_bol'] = True
            #     attached_files = request.httprequest.files.getlist('cert_of_good_conduct')
            #     for attachment in attached_files:
            #         val['cert_of_good_conduct'] = attachment.read()
            # if post.get('medical_check',False):
            #     val['medical_check_bol'] = True
            #     attached_files = request.httprequest.files.getlist('medical_check')
            #     for attachment in attached_files:
            #         val['medical_check'] = attachment.read()
            # if post.get('passport_photo',False):
            #     val['passport_photo_bol'] = True
            #     attached_files = request.httprequest.files.getlist('passport_photo')
            #     for attachment in attached_files:
            #         val['passport_photo'] = attachment.read()
            # if post.get('birthday_cert',False):
            #     val['birthday_cert_bol'] = True
            #     attached_files = request.httprequest.files.getlist('birthday_cert')
            #     for attachment in attached_files:
            #         val['birthday_cert'] = attachment.read()
            # if post.get('pledge',False):
            #     val['pledge_bol'] = True
            #     attached_files = request.httprequest.files.getlist('pledge')
            #     for attachment in attached_files:
            #         val['pledge'] = attachment.read()
            
            
            
            
                # raise UserError(val['personal_photo'])
            if not val['student_id']:
                val['birth_date'] = dateutil.parser.parse(val['birth_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['passport_issued_date'] = dateutil.parser.parse(val['passport_issued_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['passport_end_date'] = dateutil.parser.parse(val['passport_end_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['eid_end_date'] = dateutil.parser.parse(val['eid_end_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['residency_issued_date'] = dateutil.parser.parse(val['residency_issued_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['residency_end_date'] = dateutil.parser.parse(val['residency_end_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)
            val['sec_issued_date'] = dateutil.parser.parse(val['sec_issued_date']). \
                    strftime(DEFAULT_SERVER_DATE_FORMAT)

            admission_id = request.env['op.admission'].sudo().create(val)

            # admission_id.personal_photo = attached_files
            admission_id.cert_of_good_conduct = attached_files2
            admission_id.medical_check = attached_files3
            admission_id.passport_photo = attached_files4
            admission_id.birthday_cert = attached_files5
            admission_id.pledge = attached_files6


            # for attachment in attached_files:
            #     attached_file = attachment.read()
            #     admission_id.personal_photo = base64.encodestring(attached_file)
 
            # for attachment in attached_files2:
            #     attached_file = attachment.read()
            #     admission_id.cert_of_good_conduct =  base64.encodestring(attached_file)

            # for attachment in attached_files3:
            #     attached_file = attachment.read()
            #     admission_id.medical_check = base64.encodestring(attached_file)

                
            # for attachment in attached_files4:
            #     attached_file = attachment.read()
            #     admission_id.passport_photo = base64.encodestring(attached_file)

                
            # for attachment in attached_files5:
            #     attached_file = attachment.read()
            #     admission_id.birthday_cert = base64.encodestring(attached_file)
                
            # for attachment in attached_files6:
            #     attached_file = attachment.read()
            #     admission_id.pledge = base64.encodestring(attached_file)

            prod_id = False
            if register.course_id.reg_fees:
                prod_id = register.course_id.product_id.id
            else:
                return request.render(
                    "openeducat_online_admission.application_confirmed",
                    {'admission_id': admission_id})
            add_qty = 1
            set_qty = 0
            request.website.sale_get_order(force_create=1)._cart_update(
                product_id=int(prod_id), add_qty=float(add_qty),
                set_qty=float(set_qty))

            order = request.website.sale_get_order()

            if order and admission_id:
                admission_id.write({'order_id': order.id})

            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection

            if order.partner_id.id == \
                    request.website.user_id.sudo().partner_id.id:
                request.session['data'] = post
                return request.redirect('/shop/address')
            for f in self._get_mandatory_fields_billing():
                if not order.partner_id[f]:
                    request.session['data'] = post
                    return request.redirect(
                        '/shop/address?partner_id=%d' % order.partner_id.id)

            values = self.checkout_values(**post)

            if post.get('express'):
                return request.redirect('/shop/confirm_order')

            values.update({'website_sale_order': order})

            # Avoid useless rendering if called in ajax
            if post.get('xhr'):
                return 'ok'
            return request.render("website_sale.checkout", values)

        order = request.website.sale_get_order()
        if not order:
            return request.redirect("/shop")
        if order and admission_id:
            admission_id.write({'order_id': order.id})
            if request.env.uid:
                user = request.env['res.users'].browse(request.env.uid)
                partner_id = user.partner_id.id
            else:
                partner_id = request.env['res.partner'].sudo().create(post).id
            order.write({'partner_invoice_id': partner_id,
                         'partner_id': partner_id})
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection
        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.env.ref('website_sale.extra_info_option')
        if extra_step.sudo().active:
            return request.redirect("/shop/extra_info")
        return request.redirect("/shop/payment")

class SubjectRegistrationPortal(CustomerPortal):


    @http.route(['/subject/registration/create/',
                 '/subject/registration/create/<int:student_id>',
                 '/subject/registration/create/<int:page>'],
                type='http', auth="user", website=True)
    def portal_craete_subject_registration(self, student_id=None, **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])

        elective_subjects = request.env['op.subject'].sudo().search(
            [('subject_type', '=', 'elective')])
        compulsory_subjects = request.env['op.subject'].sudo().search(
            [('subject_type', '=', 'compulsory')])

        course_ids = request.env['op.course'].sudo().search([])
        year_ids = request.env['op.academic.year'].sudo().search([])
        term_ids = request.env['op.academic.term'].sudo().search([])
        course_credit = request.env['course.credit'].sudo().search([])

        lms_module = request.env['ir.module.module'].sudo().search(
            [('name', '=', 'openeducat_lms')])

        if lms_module.state != 'uninstalled':
            course_ids = request.env['op.course'].sudo().search(
                [('online_course', '!=', True)])

        batch_ids = request.env['op.batch'].sudo().search([])

        return request.render(
            "openeducat_core_enterprise."
            "openeducat_create_subject_registration",
            {'student_id': student_id,
             'subject_registration_ids': elective_subjects,
             'compulsory_registration_ids': compulsory_subjects,
             'course_ids': course_ids,
             'year_ids': year_ids,
             'term_ids': term_ids,
             'course_credit': course_credit,
             'batch_ids': batch_ids,
             'page_name': 'subject_reg_form'
             })

    @http.route(['/subject/registration/submit',
                 '/subject/registration/submit/<int:page>'],
                type='http', auth="user", website=True)
    def portal_submit_subject_registration(self, **kw):

        compulsory_subject = request.httprequest. \
            form.getlist('compulsory_subject_ids')
        elective_subject = request.httprequest. \
            form.getlist('elective_subject_ids')
        vals = {
            'student_id': kw['student_id'],
            'course_id': kw['course_id'],
            'batch_id': kw['batch_id'],
            'term_id': int(kw['term_ids']),
            # 'min_unit_load': kw['min_credit'],
            # 'max_unit_load': kw['max_credit'],
            'min_credit': kw['min_credit'],
            'max_credit': kw['max_credit'],
            'compulsory_subject_ids': [[6, 0, compulsory_subject]],
            'elective_subject_ids': [[6, 0, elective_subject]],
        }
        registration_id = request.env['op.subject.registration']
        registration_id.sudo().create(vals).action_submitted()

        return request.redirect('/subject/registration/')

    @http.route('/get/subject/mincredit', type='json', website=True, auth='user')
    def get_subject_mincredit_total(self, **kw):
        crd_lst = []
        # compulsory_subject = kw['compulsory_subject_ids']
        # compulsory_subject += kw['elective_subject_ids']

        credit_course = request.env['op.course'].sudo().search([('id', '=', int(kw.get('course_id')))])
        return credit_course.min_credit

    @http.route('/get/subject/maxcredit', type='json', website=True, auth='user')
    def get_subject_maxcredit_total(self, **kw):
        crd_lst = []
        # compulsory_subject = kw['compulsory_subject_ids']
        # compulsory_subject += kw['elective_subject_ids']

        credit_course = request.env['op.course'].sudo().search([('id', '=', int(kw.get('course_id')))])
        return credit_course.max_credit

    @http.route('/get/subject/compulsory', type='json', website=True, auth='user')
    def get_subject_compulsory_total(self, **kw):
        crd_lst = []
        # compulsory_subject =   kw['compulsory_subject_ids']
        # compulsory_subject +=  kw['elective_subject_ids']
        # raise UserError('Mohon maaf tidak bisa ..')
        credit_course = request.env['op.subject'].sudo().search([('subject_type', '=', 'compulsory'),('course_id', '=', int(kw.get('course_id')))])
        for cr in credit_course:
            crd_lst.append('<option value="%s">%s</option>'%(cr.id,cr.name))
        
        return crd_lst

    @http.route('/get/subject/subcredit', type='json', website=True, auth='user')
    def get_subject_subcredit_total(self, **kw):
        crd_lst = []
        compulsory_subject =   kw['compulsory_subject_ids']
        credit_course = request.env['op.subject'].sudo().search([('id', 'in', compulsory_subject)])
        # crd_lst.append()
        # compulsory_subject +=  kw['elective_subject_ids']
        # raise UserError('Mohon maaf tidak bisa ..')
        
        for cr in credit_course:
            crd_lst.append(cr.sub_credit)
        return sum(crd_lst)


    @http.route('/get/subject/total', type='json', website=True, auth='user')
    def get_subject_credit_total(self, **kw):
        crd_lst = []
        compulsory_subject = kw['compulsory_subject_ids']
        compulsory_subject += kw['elective_subject_ids']

        credit_course = request.env['op.subject'].sudo().search([('id', 'in', compulsory_subject)])

        for cr in credit_course:
            crd_lst.append(cr.sub_credit)
        # if credit_course.all_academic == 'general':
        #     for cre in credit_course.subject_credit:
        #         if cre.subject_id.id in compulsory_subject:
        #             crd_lst.append(cre.credit)
        # else:
        #     for cre in credit_course.sem_credit_line_id:
        #         for sub_cre in cre.subject_credit:
        #             if sub_cre.subject_id.id in compulsory_subject:
        #                 crd_lst.append(sub_cre.credit)

        return sum(crd_lst)
    
    @http.route('/get/subject/getacadmic', type='json', website=True, auth='user')
    def get_subject_getacadmic_total(self, **kw):
        crd_lst = []
        # compulsory_subject = kw['compulsory_subject_ids']
        # compulsory_subject += kw['elective_subject_ids']

        credit_course = request.env['op.course'].sudo().search([('id', '=', int(kw.get('course_id')))])
        if credit_course.acadmic_year_id:
            crd_lst.append(credit_course.acadmic_year_id.id)

        return crd_lst

    @http.route('/get/subject/getterm', type='json', website=True, auth='user')
    def get_subject_getterm_total(self, **kw):
        crd_lst = []
        # compulsory_subject = kw['compulsory_subject_ids']
        # compulsory_subject += kw['elective_subject_ids']

        credit_course = request.env['op.course'].sudo().search([('id', '=', int(kw.get('course_id')))])
        if credit_course.term_id:
            crd_lst.append(credit_course.term_id.id)

        return crd_lst