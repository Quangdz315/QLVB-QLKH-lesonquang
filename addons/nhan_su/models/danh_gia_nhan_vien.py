from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DanhGiaNhanVien(models.Model):
    _name = 'danh_gia_nhan_vien'
    _description = 'Đánh giá nhân viên'
    _order = 'nam desc, ky_danh_gia desc, nhan_vien_id'
    _rec_name = 'ten_danh_gia'

    ten_danh_gia = fields.Char("Tên đánh giá", compute='_compute_ten_danh_gia', store=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade', index=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", related='nhan_vien_id.phong_ban_id', store=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", related='nhan_vien_id.chuc_vu_id', store=True)
    nguoi_danh_gia_id = fields.Many2one('nhan_vien', string="Người đánh giá")
    ky_danh_gia = fields.Selection([
        ('thang_1', 'Tháng 1'), ('thang_2', 'Tháng 2'), ('thang_3', 'Tháng 3'),
        ('thang_4', 'Tháng 4'), ('thang_5', 'Tháng 5'), ('thang_6', 'Tháng 6'),
        ('thang_7', 'Tháng 7'), ('thang_8', 'Tháng 8'), ('thang_9', 'Tháng 9'),
        ('thang_10', 'Tháng 10'), ('thang_11', 'Tháng 11'), ('thang_12', 'Tháng 12'),
        ('quy_1', 'Quý 1'), ('quy_2', 'Quý 2'), ('quy_3', 'Quý 3'), ('quy_4', 'Quý 4'),
        ('nam', 'Cả năm'),
    ], string="Kỳ đánh giá", required=True, default='quy_1')
    nam = fields.Integer("Năm", required=True, default=lambda self: fields.Date.context_today(self).year)
    ngay_danh_gia = fields.Date("Ngày đánh giá", default=fields.Date.context_today)
    diem_kpi = fields.Float("Điểm KPI", default=0)
    diem_ky_luat = fields.Float("Điểm kỷ luật", default=0)
    diem_thai_do = fields.Float("Điểm thái độ", default=0)
    diem_ky_nang = fields.Float("Điểm kỹ năng", default=0)
    diem_trung_binh = fields.Float("Điểm trung bình", compute='_compute_diem_trung_binh', store=True)
    xep_loai = fields.Selection([
        ('xuat_sac', 'Xuất sắc'),
        ('tot', 'Tốt'),
        ('kha', 'Khá'),
        ('trung_binh', 'Trung bình'),
        ('yeu', 'Yếu'),
    ], string="Xếp loại", compute='_compute_diem_trung_binh', store=True)
    muc_tieu = fields.Text("Mục tiêu kỳ tới")
    nhan_xet = fields.Text("Nhận xét")
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('xac_nhan', 'Đã xác nhận'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True)

    @api.depends('nhan_vien_id', 'ky_danh_gia', 'nam')
    def _compute_ten_danh_gia(self):
        labels = dict(self._fields['ky_danh_gia'].selection)
        for record in self:
            employee = record.nhan_vien_id.ho_ten or 'Nhân viên'
            period = labels.get(record.ky_danh_gia, record.ky_danh_gia or '')
            record.ten_danh_gia = '%s - %s/%s' % (employee, period, record.nam or '')

    @api.depends('diem_kpi', 'diem_ky_luat', 'diem_thai_do', 'diem_ky_nang')
    def _compute_diem_trung_binh(self):
        for record in self:
            record.diem_trung_binh = (record.diem_kpi + record.diem_ky_luat + record.diem_thai_do + record.diem_ky_nang) / 4.0
            if record.diem_trung_binh >= 90:
                record.xep_loai = 'xuat_sac'
            elif record.diem_trung_binh >= 80:
                record.xep_loai = 'tot'
            elif record.diem_trung_binh >= 65:
                record.xep_loai = 'kha'
            elif record.diem_trung_binh >= 50:
                record.xep_loai = 'trung_binh'
            else:
                record.xep_loai = 'yeu'

    @api.constrains('diem_kpi', 'diem_ky_luat', 'diem_thai_do', 'diem_ky_nang', 'nam')
    def _check_scores(self):
        for record in self:
            for score in [record.diem_kpi, record.diem_ky_luat, record.diem_thai_do, record.diem_ky_nang]:
                if score < 0 or score > 100:
                    raise ValidationError("Điểm đánh giá phải nằm trong khoảng 0 đến 100.")
            if record.nam < 2000 or record.nam > 2100:
                raise ValidationError("Năm đánh giá không hợp lệ.")

    @api.constrains('nhan_vien_id', 'ky_danh_gia', 'nam')
    def _check_unique_period(self):
        for record in self:
            if self.search_count([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ky_danh_gia', '=', record.ky_danh_gia),
                ('nam', '=', record.nam),
                ('id', '!=', record.id),
            ]):
                raise ValidationError("Nhân viên đã có đánh giá trong kỳ này.")

    def action_xac_nhan(self):
        self.write({'trang_thai': 'xac_nhan'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})

    def action_dat_nhap(self):
        self.write({'trang_thai': 'nhap'})
