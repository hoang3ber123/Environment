{
    'name': 'DonVithugom',
    'version': '1.0',
    'depends': ['base', 'web'],
    'data': [
            'security/donvithugom_security.xml',
            'security/ir.model.access.csv',
            'views/donvithugom_menu.xml',
        ],
    'assets': {
        'web.assets_backend': [
            "don_vi_thu_gom/static/src/css/style.css",
            'don_vi_thu_gom/static/src/js/donvithugom_template.js',
            'don_vi_thu_gom/static/src/xml/donvithugom_template.xml',
        ],
    },
    'installable': True,
    'application': True,
}
