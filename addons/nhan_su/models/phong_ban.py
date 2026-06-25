from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PhongBan(models.Model):
    _name = 'phong_ban'
    _description = 'Phòng ban'
    _order = 'ma_phong_ban, ten_phong_ban'
    _rec_name = 'ten_phong_ban'

    active = fields.Boolean("Đang hoạt động", default=True)
    ma_phong_ban = fields.Char("Mã phòng ban", required=True, index=True)
    ten_phong_ban = fields.Char("Tên phòng ban", required=True, index=True)
    truong_phong_id = fields.Many2one(
        'nhan_vien',
        string="Trưởng phòng",
        ondelete='set null',
    )
    nhan_vien_ids = fields.One2many('nhan_vien', 'phong_ban_id', string="Nhân viên")
    so_nhan_vien = fields.Integer("Số nhân viên", compute='_compute_so_nhan_vien')
    mo_ta = fields.Text("Mô tả chức năng")

    @api.depends('nhan_vien_ids', 'nhan_vien_ids.active')
    def _compute_so_nhan_vien(self):
        for department in self:
            department.so_nhan_vien = len(department.nhan_vien_ids.filtered('active'))

    @api.constrains('ma_phong_ban')
    def _check_ma_unique(self):
        for department in self:
            if self.search_count([
                ('ma_phong_ban', '=', department.ma_phong_ban),
                ('id', '!=', department.id),
            ]):
                raise ValidationError("Mã phòng ban đã tồn tại.")
