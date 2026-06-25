from odoo import api, fields, models
from odoo.exceptions import ValidationError


class QlkhDonHang(models.Model):
    _name = 'qlkh.don_hang'
    _description = 'Đơn hàng/Dịch vụ khách hàng'
    _rec_name = 'ma_don_hang'
    _order = 'ngay_don desc, id desc'

    ma_don_hang = fields.Char("Mã đơn hàng", copy=False, readonly=True, default='Mới', index=True)
    ten_don_hang = fields.Char("Tên đơn hàng/Dịch vụ", required=True)
    khach_hang_id = fields.Many2one(
        'res.partner',
        string="Khách hàng",
        required=True,
        domain=[('is_khach_hang', '=', True)],
        ondelete='restrict',
        index=True,
    )
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    ngay_don = fields.Date("Ngày đơn hàng", default=fields.Date.context_today, required=True)
    loai_don_hang = fields.Selection([
        ('san_pham', 'Sản phẩm'),
        ('dich_vu', 'Dịch vụ'),
        ('hop_dong', 'Hợp đồng dịch vụ'),
    ], string="Loại đơn", default='dich_vu', required=True)
    gia_tri = fields.Float("Giá trị đơn hàng", required=True, default=0.0)
    da_thanh_toan = fields.Float("Đã thanh toán", compute='_compute_thanh_toan', store=True)
    con_no = fields.Float("Công nợ", compute='_compute_thanh_toan', store=True)
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('xac_nhan', 'Đã xác nhận'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, index=True)
    ngay_du_kien_hoan_thanh = fields.Date("Ngày dự kiến hoàn thành")
    ghi_chu = fields.Text("Ghi chú")
    thanh_toan_ids = fields.One2many('qlkh.thanh_toan', 'don_hang_id', string="Thanh toán")

    @api.depends('gia_tri', 'thanh_toan_ids.so_tien', 'thanh_toan_ids.trang_thai')
    def _compute_thanh_toan(self):
        for order in self:
            paid = sum(order.thanh_toan_ids.filtered(
                lambda payment: payment.trang_thai == 'xac_nhan'
            ).mapped('so_tien'))
            order.da_thanh_toan = paid
            order.con_no = max(order.gia_tri - paid, 0.0)

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        if self.khach_hang_id and not self.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = self.khach_hang_id.nhan_vien_phu_trach_id

    @api.constrains('gia_tri')
    def _check_gia_tri(self):
        for order in self:
            if order.gia_tri < 0:
                raise ValidationError("Giá trị đơn hàng không được âm.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_don_hang', 'Mới') == 'Mới':
                vals['ma_don_hang'] = self.env['ir.sequence'].next_by_code(
                    'qlkh.don_hang'
                ) or 'Mới'
            if vals.get('khach_hang_id') and not vals.get('nhan_vien_phu_trach_id'):
                customer = self.env['res.partner'].browse(vals['khach_hang_id'])
                vals['nhan_vien_phu_trach_id'] = customer.nhan_vien_phu_trach_id.id
        return super().create(vals_list)

    def action_xac_nhan(self):
        self.write({'trang_thai': 'xac_nhan'})

    def action_dang_thuc_hien(self):
        self.write({'trang_thai': 'dang_thuc_hien'})

    def action_hoan_thanh(self):
        self.write({'trang_thai': 'hoan_thanh'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})

    def action_dat_nhap(self):
        self.write({'trang_thai': 'nhap'})


class QlkhThanhToan(models.Model):
    _name = 'qlkh.thanh_toan'
    _description = 'Thanh toán khách hàng'
    _order = 'ngay_thanh_toan desc, id desc'

    name = fields.Char("Mã thanh toán", copy=False, readonly=True, default='Mới', index=True)
    don_hang_id = fields.Many2one('qlkh.don_hang', string="Đơn hàng", ondelete='cascade')
    khach_hang_id = fields.Many2one(
        'res.partner',
        string="Khách hàng",
        required=True,
        domain=[('is_khach_hang', '=', True)],
        ondelete='restrict',
        index=True,
    )
    ngay_thanh_toan = fields.Date("Ngày thanh toán", default=fields.Date.context_today, required=True)
    so_tien = fields.Float("Số tiền", required=True, default=0.0)
    phuong_thuc = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('the', 'Thẻ'),
        ('khac', 'Khác'),
    ], string="Phương thức", default='chuyen_khoan', required=True)
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('xac_nhan', 'Đã xác nhận'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, index=True)
    ghi_chu = fields.Text("Ghi chú")

    @api.onchange('don_hang_id')
    def _onchange_don_hang_id(self):
        if self.don_hang_id:
            self.khach_hang_id = self.don_hang_id.khach_hang_id

    @api.constrains('so_tien')
    def _check_so_tien(self):
        for payment in self:
            if payment.so_tien <= 0:
                raise ValidationError("Số tiền thanh toán phải lớn hơn 0.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'qlkh.thanh_toan'
                ) or 'Mới'
            if vals.get('don_hang_id') and not vals.get('khach_hang_id'):
                order = self.env['qlkh.don_hang'].browse(vals['don_hang_id'])
                vals['khach_hang_id'] = order.khach_hang_id.id
        return super().create(vals_list)

    def action_xac_nhan(self):
        self.write({'trang_thai': 'xac_nhan'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})

    def action_dat_nhap(self):
        self.write({'trang_thai': 'nhap'})
