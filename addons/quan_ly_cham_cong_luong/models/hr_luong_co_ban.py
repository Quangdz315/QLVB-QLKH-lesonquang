from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HRLuongCoBan(models.Model):
    _name = 'hr_luong_co_ban'
    _description = 'Cấu hình lương cơ bản nhân viên'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên",
        required=True,
        ondelete='cascade',
        index=True,
    )
    ma_dinh_danh = fields.Char(
        "Mã định danh",
        related='nhan_vien_id.ma_dinh_danh',
        store=True,
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
    hop_dong_id = fields.Many2one(
        'hop_dong_lao_dong',
        string="Hợp đồng áp dụng",
        domain="[('nhan_vien_id', '=', nhan_vien_id)]",
        ondelete='set null',
    )
    luong_co_ban = fields.Float("Lương cơ bản (VND)", required=True, default=0.0)
    phu_cap_an_trua = fields.Float("Phụ cấp ăn trưa", default=0.0)
    phu_cap_trach_nhiem = fields.Float("Phụ cấp trách nhiệm", default=0.0)
    ghi_chu = fields.Text("Ghi chú bổ sung")

    @api.onchange('nhan_vien_id')
    def _onchange_nhan_vien_id(self):
        if not self.nhan_vien_id:
            self.hop_dong_id = False
            return
        contract = self.env['hop_dong_lao_dong'].search([
            ('nhan_vien_id', '=', self.nhan_vien_id.id),
            ('trang_thai', '=', 'hieu_luc'),
        ], order='ngay_bat_dau desc', limit=1)
        if contract:
            self.hop_dong_id = contract
            self.luong_co_ban = contract.luong_co_ban
            self.phu_cap_trach_nhiem = contract.phu_cap

    @api.onchange('hop_dong_id')
    def _onchange_hop_dong_id(self):
        if self.hop_dong_id:
            self.nhan_vien_id = self.hop_dong_id.nhan_vien_id
            self.luong_co_ban = self.hop_dong_id.luong_co_ban
            self.phu_cap_trach_nhiem = self.hop_dong_id.phu_cap

    @api.constrains('nhan_vien_id')
    def _check_unique_employee(self):
        for config in self:
            if self.search_count([
                ('nhan_vien_id', '=', config.nhan_vien_id.id),
                ('id', '!=', config.id),
            ]):
                raise ValidationError("Mỗi nhân viên chỉ có một cấu hình lương.")

    @api.constrains('luong_co_ban', 'phu_cap_an_trua', 'phu_cap_trach_nhiem')
    def _check_non_negative_amounts(self):
        for config in self:
            if min(
                config.luong_co_ban,
                config.phu_cap_an_trua,
                config.phu_cap_trach_nhiem,
            ) < 0:
                raise ValidationError("Lương và phụ cấp không được là số âm.")
