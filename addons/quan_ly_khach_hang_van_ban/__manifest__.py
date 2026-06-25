{
    'name': 'Quản lý khách hàng và văn bản',
    'version': '1.0',
    'category': 'Customer Relationship Management',
    'summary': 'Số hóa hồ sơ khách hàng gắn với văn bản và nhân sự phụ trách',
    'description': """
Module đề tài 4: Quản lý khách hàng + Quản lý văn bản.

Tính năng chính:
- Quản lý hồ sơ khách hàng trên res.partner.
- Gắn văn bản đến/đi, hợp đồng, báo giá, tài liệu pháp lý vào hồ sơ khách hàng.
- Phân công nhân viên phụ trách hồ sơ từ module Quản lý nhân sự.
- Theo dõi trạng thái hồ sơ, ngày hiệu lực, ngày hết hạn và file đính kèm.
    """,
    'depends': ['base', 'web', 'nhan_su', 'quan_ly_van_ban'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/loai_van_ban_data.xml',
        'views/res_partner_views.xml',
        'views/res_partner_sales_views.xml',
        'views/thanh_toan_views.xml',
        'views/don_hang_views.xml',
        'views/cham_soc_views.xml',
        'views/res_partner_care_views.xml',
        'views/van_ban_views.xml',
        'views/menu.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/ql_dashboard.css',
            'quan_ly_khach_hang_van_ban/static/src/js/customer_dashboard.js',
        ],
        'web.assets_qweb': [
            'quan_ly_khach_hang_van_ban/static/src/xml/customer_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
