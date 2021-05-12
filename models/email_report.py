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
            REPORT_ID = 'climbing_gym.report_report_pdf'
            pdf = self.env.ref(REPORT_ID).render_qweb_pdf(_id)
            # pdf result is a list
            b64_pdf = base64.b64encode(pdf[0])

            # save pdf as attachment
            ATTACHMENT_NAME = "Climbing_Gym_Report_%04d" % _id
            return self.env['ir.attachment'].create({
                'name': ATTACHMENT_NAME,
                'type': 'binary',
                'datas': b64_pdf,
                'datas_fname': ATTACHMENT_NAME + '.pdf',
                'store_fname': ATTACHMENT_NAME,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/x-pdf'
            })


class ReportEmailReport(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.climbing_gym_report.email_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('Entered report get document values')
        print(docids)

        # MEMBERSHIP DATA
        _membership_status, _membership_status_totals = self._get_membership_status(docids)

        _docs = self.env['climbing_gym.email_report'].search([('id', 'in', docids)])

        return {
            'doc_ids': docids,
            'doc_model': 'climbing_gym.email_report',
            'docs': _docs,
            'access_package_sales': None,
            'event_registrations': None,
            'event_group_registrations': None,
            'membership_status': _membership_status,
            'membership_status_totals': _membership_status_totals,
            'tickets': None,
            'sales_web': None,
            'sales_pdv': None,
            'invoicing': None,

        }

    def _get_membership_status(self, report_id):

        # Membership status
        _membership_ids = self.env['climbing_gym.membership'].search([('state', '=', 'active')], order='name desc')

        _status_list = ['pending', 'active', 'overdue', 'cancel']
        _membership_status = []
        _membership_status_totals = {}

        for mss in _status_list:
            _membership_status_totals[mss] = 0

        for _membership in _membership_ids:
            _m = {'name': _membership.name}
            for mss in _status_list:
                _m[mss] = 0

            _members_ids = self.env['climbing_gym.member_membership'].search([('membership_id', '=', _membership.id)])

            for _member in _members_ids:
                _m[_member.state] = _m[_member.state] + 1
                _membership_status_totals[_member.state] = _membership_status_totals[_member.state] + 1

            _membership_status.append(_m)

        return _membership_status, _membership_status_totals
