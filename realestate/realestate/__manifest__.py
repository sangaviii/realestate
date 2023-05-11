{
    'name': "real estate",
    'author': "sangavi",
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/properties_views.xml',
        'views/properties_tags_views.xml',
        'views/property_types_views.xml',
        'views/property_users_views.xml',


    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}