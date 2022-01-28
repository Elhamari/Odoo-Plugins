
{
    'name': 'Product to assets',
    'version': '0.1',
    'category': 'Accounting',
    'author': 'Khansaa AbdElsalam',
    'company': 'Apps Gate Solutions',
    'depends': ['purchase','account_accountant','account_asset','stock'],
    'data': [
        'security/product_to_assets_security.xml',
        'security/ir.model.access.csv',
        'views/product_to_assets_views.xml',
        'views/sequence.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
