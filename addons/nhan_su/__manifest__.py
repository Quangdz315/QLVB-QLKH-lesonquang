# -*- coding: utf-8 -*-
{
    'name': 'Quản lý nhân sự',
    'summary': 'Quản lý hồ sơ nhân viên, phòng ban, chức vụ và hợp đồng lao động',
    'description': 'Hệ thống quản lý nhân sự chi tiết cho doanh nghiệp.',
    'author': 'My Company',
    'category': 'Human Resources',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/phong_ban_views.xml',
        'views/chuc_vu_views.xml',
        'views/hop_dong_lao_dong_views.xml',
        'views/nhan_vien.xml',
        'views/tuyen_dung_views.xml',
        'views/nhan_vien_mo_rong_views.xml',
        'views/danh_gia_nhan_vien_views.xml',
        'views/dao_tao_bang_cap_views.xml',
        'views/nghi_phep_views.xml',
        'views/menu.xml',
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/ql_dashboard.css',
            'nhan_su/static/src/js/hr_dashboard.js',
        ],
        'web.assets_qweb': [
            'nhan_su/static/src/xml/hr_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
}
