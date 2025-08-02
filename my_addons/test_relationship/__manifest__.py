{
    'name': 'Test relation JS App',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/test_relationship_security.xml',
            'security/ir.model.access.csv',
            'views/test_relationship_menu.xml',
        ],
    'assets': {
        'web.assets_backend': [
            "test_relationship/static/src/css/style.css",
            'test_relationship/static/src/js/test_relationship_template.js',
            'test_relationship/static/src/xml/test_relationship_template.xml',
        ],
    },
    'installable': True,
    'application': True,
}
