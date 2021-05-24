# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta, date, timezone
from odoo import models, fields, api, _

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

        # MAP SALES



        # TICKET RESERVATIONS

        # EVENT GROUP STATUS

        # MEMBERSHIP DATA
        _membership_status, _membership_status_totals = self._get_membership_status(docids)

        _membership_bar_graph = self._get_membership_bar_graph(_membership_status)

        _docs = self.env['climbing_gym.email_report'].search([('id', 'in', docids)])

        # Tickets wordcloud
        _ticket_word_cloud = self._get_ticket_wordcloud(_docs.date_start, _docs.date_end)
        _ticket_bar_graph = self._get_ticket_bar_graph(_docs.date_start, _docs.date_end)


        # Website sales


        # POS Sales


        # General invoicing



        return {
            'doc_ids': docids,
            'doc_model': 'climbing_gym.email_report',
            'docs': _docs,
            'access_package_sales': None,
            'event_registrations': None,
            'event_group_registrations': None,

            'membership_status': _membership_status,
            'membership_status_totals': _membership_status_totals,
            'membership_bar_graph': _membership_bar_graph,

            'tickets': None,
            'ticket_word_cloud': _ticket_word_cloud,
            'ticket_bar_graph': _ticket_bar_graph,

            'sales_web': None,
            'sales_pdv': None,
            'invoicing': None,

        }

    def _get_membership_status(self, report_id):

        # Membership type
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

            # find members for each status
            _members_ids = self.env['climbing_gym.member_membership'].search([('membership_id', '=', _membership.id)])

            for _member in _members_ids:
                _m[_member.state] = _m[_member.state] + 1
                _membership_status_totals[_member.state] = _membership_status_totals[_member.state] + 1

            _membership_status.append(_m)

        return _membership_status, _membership_status_totals

    def _get_membership_bar_graph(self, _membership_data):

        # Set this before anything
        matplotlib.use('Agg')
        plt.clf()

        # set heights of bars
        bars1_pending = []
        bars2_active = []
        bars3_overdue = []

        _titles = []
        _bars = {}
        for _m in _membership_data:
            _titles.append(_m['name'])

            for _key in _m:
                if 'name' in _key:
                    continue
                if 'pending' in _key:
                    bars1_pending.append(_m[_key])
                if 'active' in _key:
                    bars2_active.append(_m[_key])
                if 'overdue' in _key:
                    bars3_overdue.append(_m[_key])

        #bar width
        barWidth = 1

        # Heights of bars1 + bars2
        bars = np.add(bars1_pending, bars2_active).tolist()

        # The position of the bars on the x-axis
        r = range(0, len(_titles))

        # Create brown bars
        plt.bar(r, bars1_pending, color='#afba2f', edgecolor='white', width=barWidth, label='Pending')
        # Create green bars (middle), on top of the first ones
        plt.bar(r, bars2_active, bottom=bars1_pending, color='#557f2d', edgecolor='white', width=barWidth,
                label='Active')
        # Create green bars (top)
        plt.bar(r, bars3_overdue, bottom=bars, color='#b8312a', edgecolor='white', width=barWidth, label='Overdue')

        # Custom X axis
        plt.xticks(r, _titles, fontweight='bold')
        plt.xlabel("Membership")

        plt.legend()

        # px = 1 / plt.rcParams['figure.dpi']  # pixel in inches
        # plt.subplots(figsize=(1200 * px, 400 * px))

        # Margins
        #plt.subplots_adjust(bottom=0.3, top=0.9)



        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')



    def _get_ticket_wordcloud(self, start_date, end_date):
        # Create a list of word

        _tickets = self.env['helpdesk.ticket'].search([('create_date', '>', start_date), ('create_date', '<', end_date)])
        all_words = []

        for ticket in _tickets:
            all_words.extend(ticket.name.split(' '))

        if len(all_words) == 0:
            all_words.append(_("None"))

        # intilize a null list
        unique_list = []

        # traverse for all elements
        for x in all_words:
            # check if exists in unique_list or not
            if x not in unique_list:
                unique_list.append(x)

        text = ' '.join(unique_list)

        # Create the word cloud object
        word_cloud_object = WordCloud(width=1200, height=400, margin=0).generate(text)

        matplotlib.use('Agg')

        plt.clf()
        # Display the generated image:
        plt.imshow(word_cloud_object, interpolation='bilinear')
        plt.axis("off")
        plt.margins(x=0, y=0)

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')



    def _get_ticket_bar_graph(self, start_date, end_date):
        # Create a list of word

        # create dataset
        height = [3, 12, 5, 18, 45]
        bars = ('A', 'B', 'C', 'D', 'E')

        _tickets = self.env['helpdesk.ticket'].search([('create_date', '>', start_date), ('create_date', '<', end_date)])

        _values = {}

        for ticket in _tickets:
            if ticket.team_id.name not in _values:
                _values[ticket.team_id.name] = 0

            _values[ticket.team_id.name] += 1

        if False in _values:
            _values[_("Undefined")] = _values[False]
            _values.pop(False, None)

        height =  _values.values()
        bars = _values.keys()

        x_pos = np.arange(len(bars))

        plt.clf()

        px = 1 / plt.rcParams['figure.dpi']  # pixel in inches
        plt.subplots(figsize=(1200 * px, 400 * px))

        # Margins
        plt.subplots_adjust(bottom=0.3, top=0.9)

        # Create bars and choose color
        plt.bar(x_pos, height, color=(0.5, 0.1, 0.5, 0.6))

        # Add title and axis names
        plt.title(_("Tickets"))
        plt.xlabel(_("Categories"))
        plt.ylabel(_("Quantity"))

        # Create names on the x axis
        plt.xticks(x_pos, bars, rotation=45)


        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')
