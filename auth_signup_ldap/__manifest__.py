# -*- coding: utf-8 -*-
{
    'name': "Signup into LDAP",

    'summary': """
        Create entry in LDAP on signup
        Short (1 phrase/line) summary of the module's purpose, used as
        """,

    'description': """
        Create entry in LDAP on signup
    """,

    'author': "Golubev",
    'website': "http://www.odoo-ukraine.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['auth_signup' ,'auth_ldap'], #

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
}