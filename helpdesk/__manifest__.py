# -*- coding: utf-8 -*-
{
    'name': "HelpDesk",
    'version': "0.1",
    'author': "Golubev",
    'category': "Tools",
    'support': "golubev@svami.in.ua",
    'summary': "A helpdesk / support ticket system",
    'description': "A helpdesk / support ticket system",
    'license':'LGPL-3',
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/support_team_views.xml',
    ],
    'demo': [],
    'depends': ['mail'],
    'installable': True,
}
