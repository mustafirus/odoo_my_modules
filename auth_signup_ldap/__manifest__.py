# -*- coding: utf-8 -*-
{
    'name': "Signup into LDAP",

    'summary': """
        LDAP backend for signup
        """,

    'description': """
        Create entry in LDAP on signup or create user
        Modify password in ldap on reset password(dont store in db)
        Modify cn, givenName, sn in ldap on change name 
        Uses auth_ldap for config 
    """,

    'author': "Golubev",
    'website': "http://www.odoo-ukraine.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['auth_signup' ,'auth_ldap', 'website_portal'], #

    # always loaded
    'data': [
        'views/templates.xml',
    ],
    'external_dependencies' : {
        'python' : ['ldap'],
    }
}