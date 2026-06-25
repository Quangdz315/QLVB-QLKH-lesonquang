from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DaoTaoBangCap(models.Model):
    _name = 'dao_tao_bang_cap'
    _description = 'Đào tạo và bằng cấp nhân viên'
    _order = 'ngay_ket_thuc desc, nhan_vien_id'
    _rec_name = 'ten_chuong_trinh'

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade', index=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", related='nhan_vien_id.phong_ban_id', store=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", related='nhan_vien_id.chuc_vu_id', store=True)
    loai = fields.Selection([
        ('bang_cap', 'Bằng cấp'),
        ('chung_chi', 'Chứng chỉ'),
        ('khoa_hoc', 'Khóa đào tạo'),
        ('ky_nang', 'Kỹ năng'),
    ], string="Loại hồ sơ", default='khoa_hoc', required=True)
    ten_chuong_trinh = fields.Char("Tên chương trình/bằng cấp", required=True, index=True)
    don_vi_dao_tao = fields.Char("Đơn vị đào tạo/cấp bằng")
    chuyen_nganh = fields.Char("Chuyên ngành/Kỹ năng")
    ngay_bat_dau = fields.Date("Ngày bắt đầu")
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    ngay_het_han = fields.Date("Ngày hết hạn")
    ket_qua = fields.Char("Kết quả/Xếp loại")
    chi_phi = fields.Float("Chi phí")
    cong_ty_chi_tra = fields.Boolean("Công ty chi trả")
    tep_dinh_kem = fields.Binary("File minh chứng")
    ten_tep_dinh_kem = fields.Char("Tên file")
    trang_thai = fields.Selection([
        ('ke_hoach', 'Kế hoạch'),
        ('dang_hoc', 'Đang học'),
        ('hoan_thanh', 'Hoàn thành'),
        ('het_han', 'Hết hạn'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='ke_hoach', required=True)
    ghi_chu = fields.Text("Ghi chú")

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc', 'chi_phi')
    def _check_values(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc and record.ngay_ket_thuc < record.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu.")
            if record.chi_phi < 0:
                raise ValidationError("Chi phí không được âm.")

    def action_dang_hoc(self):
        self.write({'trang_thai': 'dang_hoc'})

    def action_hoan_thanh(self):
        self.write({'trang_thai': 'hoan_thanh'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})
