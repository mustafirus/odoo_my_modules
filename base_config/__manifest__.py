# -*- coding: utf-8 -*-
{
    'name': "base_config",
    'category': 'base',
    'version': '0.1',
    'summary': """
        Configure mail and other base settings""",
    'description': """
        Configure mail and other base settings
    """,
    'author': "golubev",
    'website': "http://www.cloud.net.ua",
    'depends': ['fetchmail'],
    'data': [
        'data/config.xml',
    ],
    'installable': True,
}