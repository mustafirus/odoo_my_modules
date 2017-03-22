# -*- coding: utf-8 -*-
{
    'name': "slot_machine_counters",
    'version': "0.1",
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
    'depends': ['base'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/hallslot.xml',
        'views/templates.xml',
        'views/slotshot.xml',
        'data/sequence.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}