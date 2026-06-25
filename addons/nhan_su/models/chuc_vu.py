from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Chức vụ'
    _order = 'ma_chuc_vu, ten_chuc_vu'
    _rec_name = 'ten_chuc_vu'

    active = fields.Boolean("Đang sử dụng", default=True)
    ma_chuc_vu = fields.Char("Mã chức vụ", required=True, index=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True, index=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", ondelete='set null')
    he_so_chuc_vu = fields.Float("Hệ số chức vụ", default=1.0)
    nhan_vien_ids = fields.One2many('nhan_vien', 'chuc_vu_id', string="Nhân viên")
    so_nhan_vien = fields.Integer("Số nhân viên", compute='_compute_so_nhan_vien')
    mo_ta = fields.Text("Mô tả công việc")

    @api.depends('nhan_vien_ids', 'nhan_vien_ids.active')
    def _compute_so_nhan_vien(self):
        for job in self:
            job.so_nhan_vien = len(job.nhan_vien_ids.filtered('active'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ma_chuc_vu'):
                vals['ma_chuc_vu'] = self.env['ir.sequence'].next_by_code(
                    'chuc_vu.ma_chuc_vu'
                ) or 'CV0000'
        return super().create(vals_list)

    @api.constrains('ma_chuc_vu')
    def _check_ma_unique(self):
        for job in self:
            if self.search_count([
                ('ma_chuc_vu', '=', job.ma_chuc_vu),
                ('id', '!=', job.id),
            ]):
                raise ValidationError("Mã chức vụ đã tồn tại.")
