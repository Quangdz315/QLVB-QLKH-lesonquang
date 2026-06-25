from odoo import api, fields, models


class NhanVien(models.Model):
    _inherit = 'nhan_vien'

    cau_hinh_luong_ids = fields.One2many(
        'hr_luong_co_ban', 'nhan_vien_id', string="Cấu hình lương"
    )
    cham_cong_ids = fields.One2many(
        'hr_cham_cong', 'nhan_vien_id', string="Chấm công"
    )
    khen_thuong_ky_luat_ids = fields.One2many(
        'hr_khen_thuong_ky_luat', 'nhan_vien_id', string="Khen thưởng/Kỷ luật"
    )
    phieu_luong_ids = fields.One2many(
        'hr_phieu_luong', 'nhan_vien_id', string="Phiếu lương"
    )
    so_ban_cham_cong = fields.Integer(compute='_compute_payroll_counts')
    so_quyet_dinh = fields.Integer(compute='_compute_payroll_counts')
    so_phieu_luong = fields.Integer(compute='_compute_payroll_counts')

    def _compute_payroll_counts(self):
        Attendance = self.env['hr_cham_cong']
        Decision = self.env['hr_khen_thuong_ky_luat']
        Payslip = self.env['hr_phieu_luong']
        for employee in self:
            employee.so_ban_cham_cong = Attendance.search_count([
                ('nhan_vien_id', '=', employee.id),
            ])
            employee.so_quyet_dinh = Decision.search_count([
                ('nhan_vien_id', '=', employee.id),
            ])
            employee.so_phieu_luong = Payslip.search_count([
                ('nhan_vien_id', '=', employee.id),
            ])

    def _action_open_related(self, action_xmlid, domain, context=None):
        self.ensure_one()
        action = self.env.ref(action_xmlid).read()[0]
        action['domain'] = domain
        action['context'] = context or {}
        return action

    def action_view_cham_cong(self):
        return self._action_open_related(
            'quan_ly_cham_cong_luong.action_hr_cham_cong',
            [('nhan_vien_id', '=', self.id)],
            {'default_nhan_vien_id': self.id},
        )

    def action_view_khen_thuong_ky_luat(self):
        return self._action_open_related(
            'quan_ly_cham_cong_luong.action_hr_khen_thuong_ky_luat',
            [('nhan_vien_id', '=', self.id)],
            {'default_nhan_vien_id': self.id},
        )

    def action_view_phieu_luong(self):
        return self._action_open_related(
            'quan_ly_cham_cong_luong.action_hr_phieu_luong',
            [('nhan_vien_id', '=', self.id)],
            {'default_nhan_vien_id': self.id},
        )
