{
    'name': 'Environment App',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/environment_security.xml',
            'security/ir.model.access.csv',
            'views/menu.xml',
            'views/service_views.xml',
            'views/servicegroup_views.xml',
            'views/location_views.xml',
            'data/env.location.csv',
            'views/address_views.xml',
        ],
    'installable': True,
    'application': True,
}
