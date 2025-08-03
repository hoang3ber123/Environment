{
    'name': 'Test JS App',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/test_security.xml',
            'security/ir.model.access.csv',
            'views/test_views.xml',
            'views/category_views.xml',
            'views/tag_views.xml',
        ],
    'installable': True,
    'application': True,
}
