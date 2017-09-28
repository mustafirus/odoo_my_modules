# -*- coding: utf-8 -*-
{
    'name': "mail_svami",
    'category': 'Discuss',
    'version': '0.1',
    'summary': """
        Configure mail for account on svami.in.ua""",
    'description': """
        Configure mail for  account on svami.in.ua
        You must have account on svami.in.ua
        need python-dnspython debian module
    """,
    'author': "Svami",
    'website': "http://www.svami.in.ua",
    'depends': ['mail'],
    'auto_install': True,
    'data': [
        'views/res_config.xml',
    ],
}