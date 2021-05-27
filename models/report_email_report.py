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

    week_days = (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday"))

    @api.model
    def _get_report_values(self, docids, data=None):
        print('Entered report get document values')
        print(docids)

        # Documents, should be only one for now
        _docs = self.env['climbing_gym.email_report'].search([('id', 'in', docids)])

        # MAP SALES
        _map_sales_data, _map_sales_data_totals = self._get_map_sales_data(_docs.date_start, _docs.date_end)
        _map_sales_graph = self._get_map_cake_graph(_map_sales_data)


        # EVENT GROUP STATUS
        _event_data = self._get_event_status(_docs.date_start, _docs.date_end)

        # MEMBERSHIP DATA
        _membership_status, _membership_status_totals = self._get_membership_status(docids)
        _membership_bar_graph = self._get_membership_bar_graph(_membership_status)

        # Tickets wordcloud
        _ticket_status, _ticket_totals, _tickets_total_closed, _tickets_total_pending = self._get_ticket_status(
            _docs.date_start, _docs.date_end)
        _ticket_word_cloud = self._get_ticket_wordcloud(_docs.date_start, _docs.date_end)
        _ticket_bar_graph = self._get_ticket_bar_graph(_docs.date_start, _docs.date_end)

        # Website sales
        # POS Sales
        _sales_data = self._get_sales_status(_docs.date_start, _docs.date_end)
        _sales_data_web_cake = self._get_sales_cake_graph(_sales_data, 'website')
        _sales_data_pos_cake = self._get_sales_cake_graph(_sales_data, 'website')


        # General invoicing

        return {
            'doc_ids': docids,
            'doc_model': 'climbing_gym.email_report',
            'docs': _docs,

            'event_data': _event_data,



            'event_group_registrations': None,

            'membership_status': _membership_status,
            'membership_status_totals': _membership_status_totals,
            'membership_bar_graph': _membership_bar_graph,

            'ticket_status': _ticket_status,
            'ticket_status_totals': _ticket_totals,
            'tickets_total_closed': _tickets_total_closed,
            'tickets_total_pending': _tickets_total_pending,

            'map_sales_data': _map_sales_data,
            'map_sales_data_totals': _map_sales_data_totals,
            'map_sales_graph': _map_sales_graph,

            'ticket_word_cloud': _ticket_word_cloud,
            'ticket_bar_graph': _ticket_bar_graph,



            'sale_data': _sales_data,
            'sales_data_web_cake': _sales_data_web_cake,
            'sales_data_pos_cake': _sales_data_pos_cake,

            'sales_pdv': None,
            'invoicing': None,

        }

    def _get_map_sales_data(self, start_date, end_date):

        _access_packages = self.env['climbing_gym.access_package'].search([('state', '=', 'confirmed')],
                                                                          order='name desc')

        _fields_list = ['amount', 'remaining']

        _map_sale_data = []
        _map_sale_data_totals = {}

        for mss in _fields_list:
            _map_sale_data_totals[mss] = 0

        for _access_package in _access_packages:
            _m = {'name': _access_package.name}

            for mss in _fields_list:
                _m[mss] = 0

            # find members for each status
            _maps = self.env['climbing_gym.member_access_package'].search(
                [('create_date', '>=', start_date), ('create_date', '<=', end_date),
                 ('access_package', '=', _access_package.id)],
                order='id asc')

            for _map in _maps:
                _m['amount'] += _map.access_credits
                _m['remaining'] += _map.remaining_credits
                _map_sale_data_totals['amount'] += _map.access_credits
                _map_sale_data_totals['remaining'] += _map.remaining_credits

            _map_sale_data.append(_m)

        return _map_sale_data, _map_sale_data_totals

    def _get_sales_status(self, start_date, end_date):
        _sales_data = {}

        # find members for each status
        _pos_orders = self.env['pos.order'].search(
            [('date_order', '>=', start_date), ('date_order', '<=', end_date),
             ('state', 'in', ['done','invoiced'])],
            order='id asc')

        _website_orders = self.env['sale.order'].search(
            [('confirmation_date', '>=', start_date), ('confirmation_date', '<=', end_date),
             ('state', 'in', ['done', 'paid', 'invoiced', 'sale'])],
            order='id asc')

        _process_data = {
            'website': _website_orders,
            'pos': _pos_orders,
        }

        _totals = {
            'total_pos' : 0,
            'total_website': 0,
            'total_qty_website': 0,
            'total_qty_pos': 0
        }

        for _domain in _process_data:
            _orders = _process_data[_domain]

            for _order in _orders:

                _lines = _order.lines if _domain == 'pos' else _order.order_line

                for _line in _lines:
                    _tmpl = _line.product_id.product_tmpl_id.id
                    _product_id = _line.product_id.id

                    if _tmpl not in _sales_data:
                        _sales_data[_tmpl] = {
                            'name': _line.product_id.product_tmpl_id.name,
                            'products': {},
                            'total_website': 0,
                            'total_pos': 0,
                            'total_qty_website': 0,
                            'total_qty_pos': 0
                        }

                    if _product_id not in _sales_data[_tmpl]['products']:
                        _sales_data[_tmpl]['products'][_product_id] = {
                            'name': _line.product_id.default_code,
                            'total_website': 0,
                            'total_pos': 0,
                            'total_qty_website': 0,
                            'total_qty_pos': 0
                        }

                _sales_data[_tmpl]['products'][_product_id]['total_%s' % _domain] += _line.price_subtotal
                _sales_data[_tmpl]['total_%s' % _domain] += _line.price_subtotal
                _totals['total_%s' % _domain] += _line.price_subtotal

                if 'pos' in _domain:
                    _sales_data[_tmpl]['products'][_product_id]['total_qty_%s' % _domain] += _line.qty
                    _sales_data[_tmpl]['total_qty_%s' % _domain] += _line.qty
                    _totals['total_qty_%s' % _domain] += _line.qty

                if 'website' in _domain:
                    _sales_data[_tmpl]['products'][_product_id]['total_qty_%s' % _domain] += _line.product_uom_qty
                    _sales_data[_tmpl]['total_qty_%s' % _domain] += _line.product_uom_qty
                    _totals['total_qty_%s' % _domain] += _line.product_uom_qty




        return {'data': _sales_data, 'totals': _totals}


    def _get_event_status(self, start_date, end_date):

        # find members for each status
        _events = self.env['event.event'].search(
            [('date_begin', '>=', start_date), ('date_begin', '<=', end_date),
             ('state', '=', 'confirm')],
            order='address_id asc, date_begin asc')

        # address_id -> name
        # seats_max -> seats_available
        # date_begin to weekday
        # date_begin date_end datetime -> time localize
        # state 'confirm'

        _event_data = {}

        for _event in _events:
            _location_name = _event.address_id.name
            _event_period = "%s %s - %s" % (
                self.week_days[_event.date_begin.weekday()],
                _event.date_begin.strftime("%H:%M"),
                _event.date_end.strftime("%H:%M")
            )

            # Has location ?
            if _location_name not in _event_data:
                _event_data[
                    _location_name] = {
                    'name': _location_name,
                    'reservations': 0,
                    'assistance': None,
                    'events': {}
                }

            # has event ?
            if _event_period not in _event_data[_location_name]['events']:
                _event_data[_location_name]['events'][_event_period] = {
                    'name': _event_period,
                    'seats_max': 0,
                    'reservations': 0,
                    'assistance': None
                }

            _event_data[_location_name]['events'][_event_period]['seats_max'] += _event.seats_max
            _event_data[_location_name]['events'][_event_period]['reservations'] += _event.seats_max - _event.seats_available

        # Calculate totals an percentage
        for _location in _event_data:
            for _event in _event_data[_location]['events']:
                _event_data[_location]['events'][_event]['assistance'] = _event_data[_location]['events'][_event]['reservations'] / (
                            _event_data[_location]['events'][_event]['seats_max'] / 100)

                _event_data[_location]['reservations'] += _event_data[_location]['events'][_event]['reservations']

                if _event_data[_location]['assistance'] is None:
                    _event_data[_location]['assistance'] = _event_data[_location]['events'][_event]['assistance']
                else:
                    _event_data[_location]['assistance'] = (_event_data[_location]['assistance'] + _event_data[_location]['events'][_event]['assistance']) / 2

        return _event_data






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

    def _get_ticket_status(self, start_date, end_date):

        _ticket_categories = self.env['helpdesk.ticket.category'].search([('active', '=', True)], order='name desc')

        # Tickets closed in the time period
        _closed_tickets = len(self.env['helpdesk.ticket'].search(
            [('closed_date', '>=', start_date), ('closed_date', '<=', end_date)], order='number desc'))

        _pending_tickets = len(self.env['helpdesk.ticket'].search([('closed_date', '=', None)], order='number desc'))

        # interested in response time, completion time

        _status_list = ['open', 'close', 'average_response']
        _ticket_status = []
        _ticket_status_totals = {}

        for mss in _status_list:
            _ticket_status_totals[mss] = 0

        for _ticket_category in _ticket_categories:
            _m = {'name': _ticket_category.name}

            for mss in _status_list:
                _m[mss] = 0

            # find members for each status
            _created_tickets = self.env['helpdesk.ticket'].search(
                [('create_date', '>=', start_date), ('create_date', '<=', end_date),
                 ('category_id', '=', _ticket_category.id)],
                order='number desc')

            for _ticket in _created_tickets:

                if _ticket.closed_date:
                    _m['close'] += 1
                    _ticket_status_totals['close'] += 1

                    delta = _ticket.closed_date - _ticket.create_date
                    days_diff = delta.days + delta.seconds / (3600 * 24)

                    if _m['average_response'] == 0:
                        _m['average_response'] = days_diff
                    else:
                        _m['average_response'] = (_m['average_response'] + days_diff) / 2

                else:
                    _m['open'] += 1

            _ticket_status_totals['open'] += _m['open']
            _ticket_status_totals['close'] += _m['close']

            _ticket_status.append(_m)

        return _ticket_status, _ticket_status_totals, _closed_tickets, _pending_tickets

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

        # bar width
        barWidth = 1

        # Heights of bars1 + bars2
        bars = np.add(bars1_pending, bars2_active).tolist()

        # The position of the bars on the x-axis
        r = range(0, len(_titles))

        # Create brown bars
        plt.bar(r, bars1_pending, color='#afba2f', edgecolor='white', width=barWidth, label=_("Pending"))
        # Create green bars (middle), on top of the first ones
        plt.bar(r, bars2_active, bottom=bars1_pending, color='#557f2d', edgecolor='white', width=barWidth,
                label=_("Active"))
        # Create green bars (top)
        plt.bar(r, bars3_overdue, bottom=bars, color='#b8312a', edgecolor='white', width=barWidth, label=_("Overdue"))

        # Custom X axis
        plt.xticks(r, _titles, fontweight='bold')
        plt.xlabel("Membership")

        plt.legend()

        # px = 1 / plt.rcParams['figure.dpi']  # pixel in inches
        # plt.subplots(figsize=(1200 * px, 400 * px))

        # Margins
        # plt.subplots_adjust(bottom=0.3, top=0.9)

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')

    def _get_ticket_wordcloud(self, start_date, end_date):
        # Create a list of word

        _tickets = self.env['helpdesk.ticket'].search(
            [('create_date', '>', start_date), ('create_date', '<', end_date)])
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
        word_cloud_object = WordCloud(width=1200, height=600, margin=0).generate(text)

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

        _tickets = self.env['helpdesk.ticket'].search(
            [('create_date', '>', start_date), ('create_date', '<', end_date)])

        _values = {}

        for ticket in _tickets:
            if ticket.category_id.name not in _values:
                _values[ticket.category_id.name] = 0

            _values[ticket.category_id.name] += 1

        if False in _values:
            _values[_("Undefined")] = _values[False]
            _values.pop(False, None)

        height = _values.values()
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

    def _get_map_cake_graph(self, _map_data):
        plt.clf()

        names = []
        values = []

        for _map in _map_data:
            names.append(_map["name"])
            values.append(_map["amount"])

        # Label distance: gives the space between labels and the center of the pie
        plt.pie(values, labels=names, labeldistance=1.15, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')


    def _get_sales_cake_graph(self, _sales_data, _domain = 'website'):
        plt.clf()

        names = []
        values = []

        for _product in _sales_data['data']:
            names.append(_sales_data['data'][_product]['name'])
            values.append(_sales_data['data'][_product]['total_%s' % _domain])

        # Label distance: gives the space between labels and the center of the pie
        plt.pie(values, labels=names, labeldistance=1.15, wedgeprops={'linewidth': 3, 'edgecolor': 'white'})

        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='png')
        my_stringIObytes.seek(0)
        return base64.b64encode(my_stringIObytes.read()).decode('utf-8')