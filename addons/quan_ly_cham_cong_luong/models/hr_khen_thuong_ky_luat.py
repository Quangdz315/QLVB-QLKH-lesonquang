from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRKhenThuongKyLuat(models.Model):
    _name = 'hr_khen_thuong_ky_luat'
    _description = 'Khen thưởng và kỷ luật nhân viên'
    _order = 'ngay_ap_dung desc'
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
    loai_quyet_dinh = fields.Selection([
        ('thuong', 'Khen thưởng'),
        ('ky_luat', 'Kỷ luật phạt'),
    ], string="Loại quyết định", required=True, default='thuong')
    so_tien = fields.Float("Số tiền", required=True, default=0.0)
    ngay_ap_dung = fields.Date(
        "Ngày áp dụng",
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    ghi_chu = fields.Text("Ghi chú")

    @api.constrains('so_tien')
    def _check_amount(self):
        for decision in self:
            if decision.so_tien <= 0:
                raise ValidationError("Số tiền thưởng/phạt phải lớn hơn 0.")
