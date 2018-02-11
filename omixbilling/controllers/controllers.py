# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, get_records_pager
from odoo.http import request


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal , self)._prepare_portal_layout_values()
        # domain is needed to hide non portal project for employee
        # portal users can't see the privacy_visibility, fetch the domain for them in sudo
        subscription_count = request.env['omixbilling.subscription'].search_count([])
        values.update({
            'subscription_count': subscription_count,
        })
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth="user", website=True)
    def my_subscriptions(self, page=1, date_begin=None, date_end=None, project=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()

        sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        domain = ([])
        order = sortings.get(sortby, sortings['date'])['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('omixbilling.subscription', [('active', '=', False)])
        # pager
        pager = request.website.pager(
            url="/my/subscriptions",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=values['subscription_count'],
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        subscriptions = request.env['omixbilling.subscription'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'sortings': sortings,
            'sortby': sortby,
            'subscriptions': subscriptions,
            'page_name': 'subscription',
            'archive_groups': archive_groups,
            'default_url': '/my/subscriptions',
            'pager': pager
        })
        return request.render("omixbilling.my_subscriptions", values)

    @http.route(['/my/subscriptions/<int:subscription_id>'], type='http', auth="user", website=True)
    def my_subscriptions_subscription(self, subscription_id=None, **kw):
        subscription = request.env['omixbilling.subscription'].browse(subscription_id)
        return request.render("omixbilling.my_subscriptions_subscription", {'subscription': subscription})

