from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NghiPhep(models.Model):
    _name = 'nghi_phep'
    _description = 'Đơn nghỉ phép nhân viên'
    _order = 'ngay_bat_dau desc, nhan_vien_id'
    _rec_name = 'ma_don'

    ma_don = fields.Char("Mã đơn", required=True, copy=False, default='Mới', index=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade', index=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", related='nhan_vien_id.phong_ban_id', store=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", related='nhan_vien_id.chuc_vu_id', store=True)
    loai_nghi = fields.Selection([
        ('nam', 'Nghỉ phép năm'),
        ('om', 'Nghỉ ốm'),
        ('thai_san', 'Thai sản'),
        ('khong_luong', 'Nghỉ không lương'),
        ('viec_rieng', 'Việc riêng'),
        ('khac', 'Khác'),
    ], string="Loại nghỉ", default='nam', required=True)
    ngay_bat_dau = fields.Date("Từ ngày", required=True, default=fields.Date.context_today)
    ngay_ket_thuc = fields.Date("Đến ngày", required=True, default=fields.Date.context_today)
    so_ngay = fields.Float("Số ngày", compute='_compute_so_ngay', store=True)
    ly_do = fields.Text("Lý do")
    nguoi_duyet_id = fields.Many2one('res.users', string="Người duyệt", readonly=True)
    ngay_duyet = fields.Datetime("Ngày duyệt", readonly=True)
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('tu_choi', 'Từ chối'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, index=True)
    ghi_chu_duyet = fields.Text("Ghi chú duyệt")

    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_so_ngay(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc and record.ngay_ket_thuc >= record.ngay_bat_dau:
                record.so_ngay = (record.ngay_ket_thuc - record.ngay_bat_dau).days + 1
            else:
                record.so_ngay = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_don', 'Mới') == 'Mới':
                vals['ma_don'] = self.env['ir.sequence'].next_by_code('nghi_phep.ma_don') or 'Mới'
        return super().create(vals_list)

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc and record.ngay_ket_thuc < record.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu.")

    def action_gui_duyet(self):
        self.write({'trang_thai': 'cho_duyet'})

    def action_duyet(self):
        self.write({
            'trang_thai': 'da_duyet',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now(),
        })

    def action_tu_choi(self):
        self.write({
            'trang_thai': 'tu_choi',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now(),
        })

    def action_huy(self):
        self.write({'trang_thai': 'huy'})

    def action_dat_nhap(self):
        self.write({'trang_thai': 'nhap'})
