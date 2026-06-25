{
    'name': 'Quản lý Chấm công & Tính lương',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Tích hợp nhân viên, hợp đồng, chấm công, thưởng phạt và phiếu lương',
    'license': 'LGPL-3',
    'depends': ['base', 'nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_luong_co_ban_views.xml',
        'views/hr_cham_cong_views.xml',
        'views/hr_khen_thuong_ky_luat_views.xml',
        'views/hr_phieu_luong_views.xml',
        'views/hr_integration_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}
