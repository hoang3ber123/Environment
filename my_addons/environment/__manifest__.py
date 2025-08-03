{
    'name': 'Environment App',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/environment_security.xml',
            'security/ir.model.access.csv',
            'views/menu.xml',
            'views/servicegroup_views.xml',
        ],
    'installable': True,
    'application': True,
}
