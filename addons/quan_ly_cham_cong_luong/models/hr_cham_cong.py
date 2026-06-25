from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRChamCong(models.Model):
    _name = 'hr_cham_cong'
    _description = 'Bảng dữ liệu chấm công hằng ngày'
    _order = 'ngay_cham_cong desc, nhan_vien_id'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên",
        required=True,
        ondelete='cascade',
        index=True,
        domain=[('active', '=', True)],
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
    ngay_cham_cong = fields.Date(
        "Ngày chấm công",
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    trang_thai = fields.Selection([
        ('di_lam', 'Đi làm đủ ngày'),
        ('nua_ngay', 'Làm nửa ngày'),
        ('nghi_co_phep', 'Nghỉ có phép'),
        ('nghi_khong_phep', 'Nghỉ không phép'),
    ], string="Trạng thái công", default='di_lam', required=True)
    so_gio_tang_ca = fields.Float("Số giờ tăng ca (OT)", default=0.0)
    nguoi_xac_nhan = fields.Char("Người kiểm tra xác nhận")

    @api.constrains('nhan_vien_id', 'ngay_cham_cong')
    def _check_unique_attendance(self):
        for attendance in self:
            if self.search_count([
                ('nhan_vien_id', '=', attendance.nhan_vien_id.id),
                ('ngay_cham_cong', '=', attendance.ngay_cham_cong),
                ('id', '!=', attendance.id),
            ]):
                raise ValidationError("Nhân viên đã được chấm công trong ngày này.")

    @api.constrains('so_gio_tang_ca')
    def _check_overtime(self):
        for attendance in self:
            if attendance.so_gio_tang_ca < 0 or attendance.so_gio_tang_ca > 24:
                raise ValidationError("Số giờ tăng ca phải nằm trong khoảng 0 đến 24 giờ.")
