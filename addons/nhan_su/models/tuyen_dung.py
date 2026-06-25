from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ViTriTuyenDung(models.Model):
    _name = 'vi_tri_tuyen_dung'
    _description = 'Vị trí tuyển dụng'
    _order = 'ngay_mo desc, ten_vi_tri'
    _rec_name = 'ten_vi_tri'

    ten_vi_tri = fields.Char("Vị trí tuyển dụng", required=True, index=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", required=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ")
    so_luong_can_tuyen = fields.Integer("Số lượng cần tuyển", default=1)
    so_ung_vien = fields.Integer("Số ứng viên", compute='_compute_so_ung_vien')
    so_da_tuyen = fields.Integer("Đã tuyển", compute='_compute_so_ung_vien')
    ngay_mo = fields.Date("Ngày mở", default=fields.Date.context_today)
    han_nop = fields.Date("Hạn nộp hồ sơ")
    muc_luong_du_kien = fields.Float("Mức lương dự kiến")
    yeu_cau = fields.Text("Yêu cầu công việc")
    mo_ta = fields.Text("Mô tả công việc")
    trang_thai = fields.Selection([
        ('mo', 'Đang tuyển'),
        ('tam_dung', 'Tạm dừng'),
        ('dong', 'Đã đóng'),
    ], string="Trạng thái", default='mo', required=True)
    ung_vien_ids = fields.One2many('ung_vien_tuyen_dung', 'vi_tri_id', string="Ứng viên")

    def _compute_so_ung_vien(self):
        for record in self:
            record.so_ung_vien = len(record.ung_vien_ids)
            record.so_da_tuyen = len(record.ung_vien_ids.filtered(lambda c: c.trang_thai == 'trung_tuyen'))

    @api.constrains('so_luong_can_tuyen', 'muc_luong_du_kien', 'ngay_mo', 'han_nop')
    def _check_values(self):
        for record in self:
            if record.so_luong_can_tuyen <= 0:
                raise ValidationError("Số lượng cần tuyển phải lớn hơn 0.")
            if record.muc_luong_du_kien < 0:
                raise ValidationError("Mức lương dự kiến không được âm.")
            if record.ngay_mo and record.han_nop and record.han_nop < record.ngay_mo:
                raise ValidationError("Hạn nộp hồ sơ phải sau ngày mở tuyển.")

    def action_mo(self):
        self.write({'trang_thai': 'mo'})

    def action_tam_dung(self):
        self.write({'trang_thai': 'tam_dung'})

    def action_dong(self):
        self.write({'trang_thai': 'dong'})


class UngVienTuyenDung(models.Model):
    _name = 'ung_vien_tuyen_dung'
    _description = 'Ứng viên tuyển dụng'
    _order = 'create_date desc'
    _rec_name = 'ho_ten'

    ho_ten = fields.Char("Họ và tên", required=True, index=True)
    vi_tri_id = fields.Many2one('vi_tri_tuyen_dung', string="Vị trí ứng tuyển", required=True, ondelete='cascade')
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", related='vi_tri_id.phong_ban_id', store=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", related='vi_tri_id.chuc_vu_id', store=True)
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    ngay_sinh = fields.Date("Ngày sinh")
    dia_chi = fields.Text("Địa chỉ")
    nguon_tuyen_dung = fields.Selection([
        ('website', 'Website'),
        ('facebook', 'Facebook'),
        ('gioi_thieu', 'Giới thiệu'),
        ('trung_tam', 'Trung tâm tuyển dụng'),
        ('khac', 'Khác'),
    ], string="Nguồn tuyển dụng", default='khac')
    ngay_nop = fields.Date("Ngày nộp", default=fields.Date.context_today)
    ngay_phong_van = fields.Datetime("Lịch phỏng vấn")
    nguoi_phong_van_id = fields.Many2one('nhan_vien', string="Người phỏng vấn")
    muc_luong_de_xuat = fields.Float("Lương đề xuất")
    diem_phong_van = fields.Float("Điểm phỏng vấn")
    cv_file = fields.Binary("CV")
    ten_cv_file = fields.Char("Tên file CV")
    nhan_vien_tao_id = fields.Many2one('nhan_vien', string="Nhân viên sau tuyển dụng", readonly=True)
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('sang_loc', 'Sàng lọc'),
        ('phong_van', 'Phỏng vấn'),
        ('trung_tuyen', 'Trúng tuyển'),
        ('tu_choi', 'Từ chối'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='moi', required=True, index=True)
    ghi_chu = fields.Text("Ghi chú")

    @api.constrains('muc_luong_de_xuat', 'diem_phong_van')
    def _check_values(self):
        for record in self:
            if record.muc_luong_de_xuat < 0:
                raise ValidationError("Lương đề xuất không được âm.")
            if record.diem_phong_van < 0 or record.diem_phong_van > 100:
                raise ValidationError("Điểm phỏng vấn phải nằm trong khoảng 0 đến 100.")

    def action_sang_loc(self):
        self.write({'trang_thai': 'sang_loc'})

    def action_phong_van(self):
        self.write({'trang_thai': 'phong_van'})

    def action_trung_tuyen(self):
        self.write({'trang_thai': 'trung_tuyen'})

    def action_tu_choi(self):
        self.write({'trang_thai': 'tu_choi'})

    def action_tao_nhan_vien(self):
        self.ensure_one()
        if self.nhan_vien_tao_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'nhan_vien',
                'view_mode': 'form',
                'res_id': self.nhan_vien_tao_id.id,
            }
        employee = self.env['nhan_vien'].create({
            'ho_ten': self.ho_ten,
            'email': self.email,
            'so_dien_thoai': self.so_dien_thoai,
            'ngay_sinh': self.ngay_sinh,
            'dia_chi_tam_tru': self.dia_chi,
            'phong_ban_id': self.phong_ban_id.id,
            'chuc_vu_id': self.chuc_vu_id.id,
            'trang_thai': 'thu_viec',
            'loai_nhan_vien': 'thu_viec',
        })
        self.write({'nhan_vien_tao_id': employee.id, 'trang_thai': 'trung_tuyen'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nhan_vien',
            'view_mode': 'form',
            'res_id': employee.id,
        }
