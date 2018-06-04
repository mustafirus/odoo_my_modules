# -*- coding: utf-8 -*-
{
    'name': "slot_machine_counters",
    'version': '2.1',
    'author': "Golubev",
    'license':'OPL-1',
    'summary': """
        Check slot machine counters
    """,
    'description': """
        Check slot machine counters
    """,
    'website': "http://www.oduist.com.ua",
    'category': 'Tools',
    'version': '0.1',
    'depends': ['base', 'mail', 'report'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/hallslot.xml',
        'views/slotshot.xml',
        'views/report.xml',
        'views/templates.xml',
        'data/sequence.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}