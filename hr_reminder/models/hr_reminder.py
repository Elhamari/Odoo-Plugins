# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields,api,_
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta 
from datetime import  timedelta, tzinfo, time, date, datetime
from odoo.http import request

class HrPopupReminder(models.Model):
    _name = 'hr.reminder'

    name = fields.Char(string='Title', required=True)
    model_name = fields.Many2one('ir.model', help="Choose the model name", string="Model", required=True, ondelete='cascade', domain="[('model', 'like','hr')]")
    model_field = fields.Many2one('ir.model.fields', string='Field', help="Choose the field",
                                  domain="[('model_id', '=',model_name),('ttype', 'in', ['datetime','date'])]",
                                  required=True, ondelete='cascade')
    search_by = fields.Selection([('today', 'Today'),
                                  ('set_period', 'Set Period'),
                                  ('set_date', 'Set Date'), ],
                                 required=True, string="Search By")
    days_before = fields.Integer(string='Reminder before', help="NUmber of days before the reminder")
    active = fields.Boolean(string="Active", default=True)
    # exclude_year = fields.Boolean(string="Consider day alone")
    reminder_active = fields.Boolean(string="Reminder Active", help="Reminder active")
    date_set = fields.Date(string='Select Date', help="Select the reminder set date")
    date_from = fields.Date(string="Start Date", help="Start date")
    date_to = fields.Date(string="End Date", help="End date")
    expiry_date = fields.Date(string="Reminder Expiry Date", help="Expiry date")
    company_id = fields.Many2one('res.company', string='Company', required=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    creator = fields.Many2one('res.users',string="creator")

    @api.model
    def create(self,vals):
        vals['creator'] = self.env.uid
        return super(HrPopupReminder,self).create(vals)

    def reminder_scheduler(self):
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = fields.Date.today()
        obj = self.env['hr.reminder'].search([])
        
        for i in obj:
            model_ref = i.model_name.model
            field_ref = i.model_field.name
            if i.search_by != "today":
                if i.expiry_date and datetime.strptime(str(today), "%Y-%m-%d") == datetime.strptime(str(i.expiry_date), "%Y-%m-%d"):
                    i.active = False
                else:
                        if i.search_by == "set_date":
                            d1 = datetime.strptime(str(i.date_set), "%Y-%m-%d")
                            d2 = datetime.strptime(str(today), "%Y-%m-%d")
                            daydiff = abs((d2 - d1).days)
                            if daydiff <= i.days_before:
                                i.reminder_active = True
                                model = self.env['%s'%model_ref].search([])
                                for mo in model:
                                    if mo['%s'%field_ref]:
                                        f_date = datetime.strptime(str(mo['%s'%field_ref]), "%Y-%m-%d") - relativedelta(days=i.days_before)
                                        t_today = datetime.strptime(str(today), "%Y-%m-%d")
                                        # raise UserError('%s =======>  %s'%(f_date.strftime("%m-%d"),today.strftime("%m-%d")))
                                        if i.days_before != 0:
                                            if f_date.strftime("%m-%d") == t_today.strftime("%m-%d"):
                                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                                template_values = {
                                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                                    'email_cc': False,
                                                    'auto_delete': True,
                                                    'partner_to': False,
                                                    'scheduled_date': False,
                                                    'subject': 'HR Reminder',
                                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                                }
                                                template.write(template_values)
                                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)   
                                        else:
                                            if mo['%s'%field_ref].strftime("%m-%d") == t_today.strftime("%m-%d"):
                                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                                template_values = {
                                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                                    'email_cc': False,
                                                    'auto_delete': True,
                                                    'partner_to': False,
                                                    'scheduled_date': False,
                                                    'subject': 'HR Reminder',
                                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                                }
                                                template.write(template_values)
                                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)
                            else:
                                i.reminder_active = False
                        elif i.search_by == "set_period":
                            d1 = datetime.strptime(str(i.date_from), "%Y-%m-%d")
                            d2 = datetime.strptime(str(today), "%Y-%m-%d")
                            daydiff = abs((d2 - d1).days)
                            if daydiff <= i.days_before:
                                i.reminder_active = True
                                model = self.env['%s'%model_ref].search([])
                                for mo in model:
                                    if mo['%s'%field_ref]:
                                        f_date = datetime.strptime(str(mo['%s'%field_ref]), "%Y-%m-%d") - relativedelta(days=i.days_before)
                                        t_today = datetime.strptime(str(today), "%Y-%m-%d")
                                        # raise UserError('%s =======>  %s'%(f_date.strftime("%m-%d"),today.strftime("%m-%d")))
                                        if i.days_before != 0:
                                            if f_date.strftime("%m-%d") == t_today.strftime("%m-%d"):
                                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                                template_values = {
                                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                                    'email_cc': False,
                                                    'auto_delete': True,
                                                    'partner_to': False,
                                                    'scheduled_date': False,
                                                    'subject': 'HR Reminder',
                                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                                }
                                                template.write(template_values)
                                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)   
                                        else:
                                            if mo['%s'%field_ref].strftime("%m-%d") == t_today.strftime("%m-%d"):
                                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                                template_values = {
                                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                                    'email_cc': False,
                                                    'auto_delete': True,
                                                    'partner_to': False,
                                                    'scheduled_date': False,
                                                    'subject': 'HR Reminder',
                                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                                }
                                                template.write(template_values)
                                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)
                            else:
                                i.reminder_active = False
            else:
                i.reminder_active = True
                model = self.env['%s'%model_ref].search([])
                for mo in model:
                    if mo['%s'%field_ref]:
                        f_date = datetime.strptime(str(mo['%s'%field_ref]), "%Y-%m-%d") - relativedelta(days=i.days_before)
                        t_today = datetime.strptime(str(today), "%Y-%m-%d")
                        # raise UserError('%s =======>  %s'%(f_date.strftime("%m-%d"),today.strftime("%m-%d")))
                        if i.days_before != 0:
                            if f_date.strftime("%m-%d") == t_today.strftime("%m-%d"):
                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                template_values = {
                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                    'email_cc': False,
                                    'auto_delete': True,
                                    'partner_to': False,
                                    'scheduled_date': False,
                                    'subject': 'HR Reminder',
                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                }
                                template.write(template_values)
                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)   
                        else:
                            if mo['%s'%field_ref].strftime("%m-%d") == t_today.strftime("%m-%d"):
                                template = self.env.ref('hr_reminder.mail_template_user_hr_reminder_created')
                                template_values = {
                                    'email_to': self.env['hr.employee'].search([('user_id','=',i.creator.id)])[0].work_email,
                                    'email_cc': False,
                                    'auto_delete': True,
                                    'partner_to': False,
                                    'scheduled_date': False,
                                    'subject': 'HR Reminder',
                                    'body_html': """ <div >
                    
                                                                <strong>Dear  %s</strong> <br/><br/>

                                                                this is to notify you of Reminder %s for %s </br><br/>
                                                            

                                                                <strong>Thanks</strong><br/>
                                                            
                                                        </div>""" %(i.creator.name,i.name,mo.name or mo.id),
                                }
                                template.write(template_values)
                                template.send_mail(i.creator.id, force_send=True, raise_exception=True)
