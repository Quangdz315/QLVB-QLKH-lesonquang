{
    'name': 'Quản lý văn bản',
    'version': '1.0',
    'category': 'Document Management',
    'depends': ['base', 'base_setup', 'web', 'nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'views/loai_van_ban_views.xml',
        'views/van_ban_den_views.xml',
        'views/van_ban_di_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_assistant_views.xml',
        'views/menu.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/ql_dashboard.css',
            'quan_ly_van_ban/static/src/js/document_dashboard.js',
            'quan_ly_van_ban/static/src/js/ai_assistant_widget.js',
            'quan_ly_van_ban/static/src/css/ai_assistant_widget.css',
        ],
        'web.assets_qweb': [
            'quan_ly_van_ban/static/src/xml/document_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
