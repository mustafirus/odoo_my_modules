# -*- coding: utf-8 -*-
from time import mktime


from odoo import fields
import json
import urllib2
import logging
import werkzeug.urls

GAMBLING_ENDPOINT = 'http://rrd.odoo.bla:4000'

_logger = logging.getLogger(__name__)

def get_data_rrd(devid, date_beg, date_end):
    url = GAMBLING_ENDPOINT + '/counters?'
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    date_b = fields.Datetime.from_string(date_beg)
    date_e = fields.Datetime.from_string(date_end)
    date_b = int(mktime(date_b.timetuple()))
    date_e = int(mktime(date_e.timetuple()))

    reqargs = werkzeug.url_encode({
        'dateB': date_b,
        'dateE': date_e,
        'devid': devid,
    })
    try:
        req = urllib2.Request(url + reqargs, None, headers)
        content = urllib2.urlopen(req, timeout=200).read()
    except urllib2.HTTPError:
        raise
    content = json.loads(content)
    err = content.get('error')
    if err:
        e = urllib2.HTTPError(req.get_full_url(), 999, err, headers, None)
        raise e
    return content


