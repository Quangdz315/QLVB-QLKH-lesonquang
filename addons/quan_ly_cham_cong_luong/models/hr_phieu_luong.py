from calendar import monthrange
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRPhieuLuong(models.Model):
    _name = 'hr_phieu_luong'
    _description = 'Phiếu lương tháng nhân viên'
    _order = 'nam desc, thang desc, nhan_vien_id'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên",
        required=True,
        ondelete='cascade',
        index=True,
    )
    phong_ban_id = fields.Many2one(
        'phong_ban',
        string="Phòng ban",
        related='nhan_vien_id.phong_ban_id',
        store=True,
    )
    chuc_vu_id = fields.Many2one(
        'chuc_vu',
        string="Chức vụ",
        related='nhan_vien_id.chuc_vu_id',
        store=True,
    )
    thang = fields.Integer("Tháng", required=True, default=lambda self: date.today().month)
    nam = fields.Integer("Năm", required=True, default=lambda self: date.today().year)
    hop_dong_id = fields.Many2one(
        'hop_dong_lao_dong',
        string="Hợp đồng áp dụng",
        compute='_compute_thuc_linh',
    )
    nguon_luong = fields.Selection([
        ('hop_dong', 'Hợp đồng lao động'),
        ('cau_hinh', 'Cấu hình lương'),
        ('chua_co', 'Chưa có dữ liệu lương'),
    ], string="Nguồn lương", compute='_compute_thuc_linh')
    so_ngay_di_lam = fields.Float(
        "Số ngày đi làm thực tế",
        compute='_compute_thuc_linh',
    )
    so_gio_tang_ca = fields.Float(
        "Tổng giờ tăng ca",
        compute='_compute_thuc_linh',
    )
    luong_co_ban = fields.Float(
        "Lương cơ bản",
        compute='_compute_thuc_linh',
    )
    phu_cap = fields.Float(
        "Phụ cấp",
        compute='_compute_thuc_linh',
    )
    tong_khen_thuong = fields.Float(
        "Khen thưởng",
        compute='_compute_thuc_linh',
    )
    tong_ky_luat = fields.Float(
        "Kỷ luật",
        compute='_compute_thuc_linh',
    )
    thuc_linh = fields.Float(
        "Thực lĩnh",
        compute='_compute_thuc_linh',
    )
    ghi_chu = fields.Text("Ghi chú")

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_thuc_linh(self):
        SalaryConfig = self.env['hr_luong_co_ban']
        Contract = self.env['hop_dong_lao_dong']
        Attendance = self.env['hr_cham_cong']
        Decision = self.env['hr_khen_thuong_ky_luat']

        for payslip in self:
            payslip.hop_dong_id = False
            payslip.nguon_luong = 'chua_co'
            payslip.so_ngay_di_lam = 0.0
            payslip.so_gio_tang_ca = 0.0
            payslip.luong_co_ban = 0.0
            payslip.phu_cap = 0.0
            payslip.tong_khen_thuong = 0.0
            payslip.tong_ky_luat = 0.0
            payslip.thuc_linh = 0.0

            if not payslip.nhan_vien_id or not payslip.thang or not payslip.nam:
                continue
            if payslip.thang < 1 or payslip.thang > 12:
                continue

            date_from = fields.Date.to_date(
                '%s-%02d-01' % (payslip.nam, payslip.thang)
            )
            last_day = monthrange(payslip.nam, payslip.thang)[1]
            date_to = fields.Date.to_date(
                '%s-%02d-%02d' % (payslip.nam, payslip.thang, last_day)
            )

            contract = Contract.search([
                ('nhan_vien_id', '=', payslip.nhan_vien_id.id),
                ('trang_thai', '=', 'hieu_luc'),
                ('ngay_bat_dau', '<=', date_to),
                '|',
                ('ngay_ket_thuc', '=', False),
                ('ngay_ket_thuc', '>=', date_from),
            ], order='ngay_bat_dau desc', limit=1)
            config = SalaryConfig.search([
                ('nhan_vien_id', '=', payslip.nhan_vien_id.id),
            ], limit=1)

            if contract:
                payslip.hop_dong_id = contract
                payslip.nguon_luong = 'hop_dong'
                payslip.luong_co_ban = contract.luong_co_ban
                payslip.phu_cap = contract.phu_cap
                if config:
                    payslip.phu_cap += config.phu_cap_an_trua
            elif config:
                payslip.nguon_luong = 'cau_hinh'
                payslip.luong_co_ban = config.luong_co_ban
                payslip.phu_cap = (
                    config.phu_cap_an_trua + config.phu_cap_trach_nhiem
                )

            attendances = Attendance.search([
                ('nhan_vien_id', '=', payslip.nhan_vien_id.id),
                ('ngay_cham_cong', '>=', date_from),
                ('ngay_cham_cong', '<=', date_to),
            ])
            payslip.so_ngay_di_lam = sum(
                1.0 if line.trang_thai == 'di_lam'
                else 0.5 if line.trang_thai == 'nua_ngay'
                else 0.0
                for line in attendances
            )
            payslip.so_gio_tang_ca = sum(attendances.mapped('so_gio_tang_ca'))

            decisions = Decision.search([
                ('nhan_vien_id', '=', payslip.nhan_vien_id.id),
                ('ngay_ap_dung', '>=', date_from),
                ('ngay_ap_dung', '<=', date_to),
            ])
            payslip.tong_khen_thuong = sum(
                line.so_tien for line in decisions
                if line.loai_quyet_dinh == 'thuong'
            )
            payslip.tong_ky_luat = sum(
                line.so_tien for line in decisions
                if line.loai_quyet_dinh == 'ky_luat'
            )

            payslip.thuc_linh = (
                (payslip.luong_co_ban / 26.0) * payslip.so_ngay_di_lam
                + payslip.phu_cap
                + payslip.tong_khen_thuong
                - payslip.tong_ky_luat
            )

    @api.constrains('thang', 'nam')
    def _check_period(self):
        for payslip in self:
            if payslip.thang < 1 or payslip.thang > 12:
                raise ValidationError("Tháng phải nằm trong khoảng từ 1 đến 12.")
            if payslip.nam < 2000 or payslip.nam > 2100:
                raise ValidationError("Năm tính lương không hợp lệ.")

    @api.constrains('nhan_vien_id', 'thang', 'nam')
    def _check_unique_payslip(self):
        for payslip in self:
            if self.search_count([
                ('nhan_vien_id', '=', payslip.nhan_vien_id.id),
                ('thang', '=', payslip.thang),
                ('nam', '=', payslip.nam),
                ('id', '!=', payslip.id),
            ]):
                raise ValidationError(
                    "Nhân viên đã có phiếu lương trong tháng này."
                )
