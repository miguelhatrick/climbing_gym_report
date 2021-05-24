# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta, date, timezone

import pytz

from odoo import models, fields, api
from dateutil import relativedelta

class EmailReport(models.Model):
    """Reports generated for email"""
    _name = 'climbing_gym.email_report'
    _description = 'Reports generated for email'
    _inherit = ['mail.thread']

    months_choices = []
    years_choices = []
    week_choices = []
    currentYear = datetime.now().year

    for i in range(1, 13):
        months_choices.append((i, date(currentYear, i, 1).strftime('%B')))

    for i in range(currentYear, currentYear + 5):
        years_choices.append((i, str(i)))

    for i in range(1, 54):
        week_choices.append((i, str(i)))

    name = fields.Char("Name", required=True)

    # TODO: Make the title shorter
    status_selection = [('pending', "Pending"), ('built', "Built")]

    month = fields.Selection(months_choices, 'Month', required=False, default=None)
    year = fields.Selection(years_choices, 'Year', required=False, default=None)

    week_number = fields.Selection(week_choices, "Week number", required=False, default=None)

    date_start = fields.Datetime("Report start", required=False, default=None)
    date_end = fields.Datetime("Report end", required=False, default=None)

    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,
                               default=lambda self: self.env.user.tz or 'UTC')

    state = fields.Selection(status_selection, 'Status', default='pending')

    @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    @api.multi
    def action_built(self):
        self.write({'state': 'built'})

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]



    @api.onchange('month', 'year')
    def calculate_month_dates(self):
        """Calculates the start and end date for the selected month"""

        if not self.year or not self.month:
            return

        self.week_number = False

        _tz = pytz.timezone(self.date_tz)

        _temp = "%d-M%d-1" % (self.year, int(self.month))

        _date_start = _tz.localize(datetime.strptime(_temp, "%Y-M%m-%w"))
        _date_end = _date_start + relativedelta.relativedelta(months=1) - timedelta(seconds=1)

        # Convert to UTC before adding
        self.date_start = (_date_start.astimezone(pytz.utc)).replace(tzinfo=None)
        self.date_end = (_date_end.astimezone(pytz.utc)).replace(tzinfo=None)

    @api.onchange('week_number', 'year')
    def calculate_week_dates(self):
        """Calculates the start and end date for the selected week"""

        if not self.year or not self.week_number:
            return

        self.month = False

        _tz = pytz.timezone(self.date_tz)

        _temp = "%d-W%d-1" % (self.year, int(self.week_number) - 1)
        _date_start = _tz.localize(datetime.strptime(_temp, "%Y-W%W-%w"))
        _date_end = _date_start + timedelta(days=7) - timedelta(seconds=1)

        # Convert to UTC before adding
        self.date_start = (_date_start.astimezone(pytz.utc)).replace(tzinfo=None)
        self.date_end = (_date_end.astimezone(pytz.utc)).replace(tzinfo=None)


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