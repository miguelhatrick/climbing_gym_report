# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta, date, timezone
from odoo import models, fields, api

from wordcloud import WordCloud
import matplotlib

import matplotlib.pyplot as plt
import io

import numpy as np


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

        # Tickets wordcloud
        _ticket_wordcloud = self._get_ticket_wordcloud()
        _ticket_bar_graph = self._get_ticket_bar_graph()

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
            'ticket_wordcloud': _ticket_wordcloud,
            'ticket_bar_graph': _ticket_bar_graph,
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

    def _get_ticket_wordcloud(self):
        # Create a list of word

        _tickets = self.env['helpdesk.ticket'].search([('id', '>', 1)])
        allwords = []

        for ticket in _tickets:
            allwords.extend(ticket.name.split(' '))

        # intilize a null list
        unique_list = []

        # traverse for all elements
        for x in allwords:
            # check if exists in unique_list or not
            if x not in unique_list:
                unique_list.append(x)

        text = ' '.join(unique_list)

        # text = ("Python Python Python Matplotlib")

        # Create the wordcloud object
        wordcloud = WordCloud(width=800, height=500, margin=0).generate(text)

        matplotlib.use('Agg')

        plt.clf()
        # Display the generated image:
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.margins(x=0, y=0)

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')



    def _get_ticket_bar_graph(self):
        # Create a list of word

        # create dataset
        height = [3, 12, 5, 18, 45]
        bars = ('A', 'B', 'C', 'D', 'E')

        _tickets = self.env['helpdesk.ticket'].search([('id', '>', 1)])

        _values = {}

        for ticket in _tickets:
            if ticket.team_id.name not in _values:
                _values[ticket.team_id.name] = 0

            _values[ticket.team_id.name] += 1

        if False in _values:
            _values['Undefined'] = _values[False]
            _values.pop(False, None)

        height =  _values.values()
        bars = _values.keys()

        x_pos = np.arange(len(bars))

        plt.clf()
        # Create bars and choose color
        plt.bar(x_pos, height, color=(0.5, 0.1, 0.5, 0.6))

        # Add title and axis names
        plt.title('Tickets')
        plt.xlabel('categories')
        plt.ylabel('quantity')

        # Create names on the x axis
        plt.xticks(x_pos, bars)

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')
