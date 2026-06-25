from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HopDongLaoDong(models.Model):
    _name = 'hop_dong_lao_dong'
    _description = 'Hợp đồng lao động'
    _order = 'ngay_bat_dau desc, ma_hop_dong desc'
    _rec_name = 'ma_hop_dong'

    ma_hop_dong = fields.Char(
        "Mã hợp đồng",
        required=True,
        copy=False,
        readonly=True,
        default='Mới',
        index=True,
    )
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
    loai_hop_dong = fields.Selection([
        ('thu_viec', 'Hợp đồng thử việc'),
        ('xac_dinh_thoi_han', 'Hợp đồng xác định thời hạn'),
        ('khong_xac_dinh_thoi_han', 'Hợp đồng không xác định thời hạn'),
        ('thoi_vu', 'Hợp đồng thời vụ'),
        ('cong_tac_vien', 'Hợp đồng cộng tác viên'),
    ], string="Loại hợp đồng", required=True, default='thu_viec')
    ngay_ky = fields.Date("Ngày ký", default=fields.Date.context_today)
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True, default=fields.Date.context_today)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")
    luong_co_ban = fields.Float("Lương cơ bản", required=True, default=0.0)
    phu_cap = fields.Float("Tổng phụ cấp", default=0.0)
    tong_thu_nhap = fields.Float("Thu nhập thỏa thuận", compute='_compute_tong_thu_nhap', store=True)
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('hieu_luc', 'Đang hiệu lực'),
        ('het_han', 'Hết hạn'),
        ('cham_dut', 'Đã chấm dứt'),
    ], string="Trạng thái", default='nhap', required=True, index=True)
    tep_hop_dong = fields.Binary("Tệp hợp đồng", attachment=True)
    ten_tep_hop_dong = fields.Char("Tên tệp")
    ghi_chu = fields.Text("Điều khoản/Ghi chú")

    @api.depends('luong_co_ban', 'phu_cap')
    def _compute_tong_thu_nhap(self):
        for contract in self:
            contract.tong_thu_nhap = contract.luong_co_ban + contract.phu_cap

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_hop_dong', 'Mới') == 'Mới':
                vals['ma_hop_dong'] = self.env['ir.sequence'].next_by_code(
                    'hop_dong_lao_dong.ma_hop_dong'
                ) or 'Mới'
        return super().create(vals_list)

    @api.constrains('ngay_ky', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for contract in self:
            if (
                contract.ngay_ket_thuc
                and contract.ngay_bat_dau
                and contract.ngay_ket_thuc < contract.ngay_bat_dau
            ):
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu.")
            if (
                contract.ngay_ky
                and contract.ngay_ket_thuc
                and contract.ngay_ket_thuc < contract.ngay_ky
            ):
                raise ValidationError("Ngày kết thúc phải sau ngày ký.")

    def action_hieu_luc(self):
        self.write({'trang_thai': 'hieu_luc'})

    def action_het_han(self):
        self.write({'trang_thai': 'het_han'})

    def action_cham_dut(self):
        self.write({'trang_thai': 'cham_dut'})

    def action_ve_nhap(self):
        self.write({'trang_thai': 'nhap'})
