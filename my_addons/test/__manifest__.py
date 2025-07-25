{
    'name': 'Test JS App',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/test_security.xml',
            'security/ir.model.access.csv',
            'views/test_menu.xml',
        ],
    'assets': {
        'web.assets_backend': [
            "test/static/src/css/style.css",
            'test/static/src/js/test_template.js',
            'test/static/src/xml/test_template.xml',
        ],
    },
    'installable': True,
    'application': True,
}
