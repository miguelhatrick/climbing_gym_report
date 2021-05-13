# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta, date, timezone
from odoo import models, fields, api


class EmailReport(models.Model):
    """Reports generated for email"""
    _name = 'climbing_gym.email_report'
    _description = 'Reports generated for email'
    _inherit = ['mail.thread']

    months_choices = []
    years_choices = []
    currentYear = datetime.now().year

    for i in range(1, 13):
        months_choices.append((i, date(currentYear, i, 1).strftime('%B')))

    for i in range(currentYear, currentYear + 5):
        years_choices.append((i, str(i)))

    name = fields.Char("Name", required=True)

    # TODO: Make the title shorter
    status_selection = [('pending', "Pending"), ('built', "Built")]

    month = fields.Selection(months_choices, 'Month', required=True)
    year = fields.Selection(years_choices, 'Year', required=True)

    week_number = fields.Integer("Week number", required=False, default=None)

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_built(self):
        self.write({'state': 'built'})

    @api.multi
    def action_generate_attachment(self):
        for _id in self.ids:
            """ this method called from button action in view xml """
            # generate pdf from report, use report's id as reference

            test = self.create_mass_mailing(_id)

            pdf = self.env.ref('climbing_gym.email_report_report_pdf').render_qweb_pdf(_id)
            # pdf result is a list
            b64_pdf = base64.b64encode(pdf[0])

            # save pdf as attachment
            _attachment_name = "Climbing_Gym_Report_%04d" % _id
            return self.env['ir.attachment'].create({
                'name': _attachment_name,
                'type': 'binary',
                'datas': b64_pdf,
                'datas_fname': _attachment_name + '.pdf',
                'store_fname': _attachment_name,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/x-pdf'
            })

    def create_mass_mailing(self, _id):

        html = self.env.ref('climbing_gym.email_report_web').render_qweb_html([_id])
        # pdf result is a list
        # html = base64.b64encode(pdf[0])

        _send_date = datetime.now() + timedelta(minutes=5)


        test = self.env['mail.mass_mailing'].create({
            'name': 'TEST GUEROOOO',
            'body_html': html[0].decode('utf-8'),
            'state': 'in_queue',
            'schedule_date': _send_date,
            'contact_list_ids': [(6, 0, [self.env.ref('climbing_gym_report.mass_mail_list_weekly_report_climbing_gym').id])],
        })
        return test
