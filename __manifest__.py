# -*- coding: utf-8 -*-
{
    'name': "rod_inventory_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'stock','res_users'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/point_of_sale_view.xml',
        'views/production_lot_views.xml',
        'views/point_of_sale_report.xml',
        'views/report_saledetails.xml',
        'wizard/pos_details.xml',
        'views/product_views.xml',

    ],

}
