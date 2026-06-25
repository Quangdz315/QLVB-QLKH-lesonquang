from odoo import api, fields, models
from odoo.exceptions import ValidationError


DOCUMENT_GROUPS = [
    ('hop_dong', 'Hợp đồng'),
    ('bao_gia', 'Báo giá'),
    ('phap_ly', 'Tài liệu pháp lý'),
    ('bien_ban', 'Biên bản làm việc'),
    ('khac', 'Khác'),
]

DOCUMENT_STATES = [
    ('nhap', 'Bản nháp'),
    ('dang_xu_ly', 'Đang xử lý'),
    ('hoan_thanh', 'Hoàn thành'),
    ('het_han', 'Hết hạn'),
]

RECIPIENT_TYPES = [
    ('khach_hang', 'Khách hàng'),
    ('nhan_vien', 'Nhân viên'),
]


class VanBanDen(models.Model):
    _inherit = 'van_ban_den'

    khach_hang_id = fields.Many2one(
        'res.partner',
        string="Khách hàng",
        domain=[('is_khach_hang', '=', True)],
        index=True,
    )
    loai_nguoi_nhan = fields.Selection(
        RECIPIENT_TYPES,
        string="Loại người nhận",
        default='khach_hang',
        required=True,
    )
    nhan_vien_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên phụ trách",
    )
    nhom_ho_so = fields.Selection(
        DOCUMENT_GROUPS,
        string="Nhóm hồ sơ",
        default='khac',
        required=True,
    )
    ngay_hieu_luc = fields.Date(string="Ngày hiệu lực")
    ngay_het_han = fields.Date(string="Ngày hết hạn")
    trang_thai_ho_so = fields.Selection(
        DOCUMENT_STATES,
        string="Trạng thái hồ sơ",
        default='nhap',
        required=True,
    )
    tep_dinh_kem_ids = fields.Many2many(
        'ir.attachment',
        'van_ban_den_ir_attachment_rel',
        'van_ban_den_id',
        'attachment_id',
        string="Tệp đính kèm",
    )

    nguoi_nhan_phan_loai = fields.Char(
        string="Người nhận",
        compute='_compute_nguoi_nhan_phan_loai',
    )

    def _get_nguoi_nhan_parts(self):
        self.ensure_one()
        parts = []
        customer_names = []
        if self.khach_hang_id:
            customer_names.append(self.khach_hang_id.display_name)
        if 'khach_hang_nhan_ids' in self._fields:
            customer_names += [
                name for name in self.khach_hang_nhan_ids.mapped('display_name')
                if name not in customer_names
            ]
        parts += ["%s (khách hàng)" % name for name in customer_names]

        employee_names = []
        if 'nhan_vien_nhan_ids' in self._fields:
            employee_names = self.nhan_vien_nhan_ids.mapped('display_name')
        parts += ["%s (nhân viên)" % name for name in employee_names]

        note = False
        if 'nguoi_nhan' in self._fields:
            note = self.nguoi_nhan
        elif 'noi_nhan' in self._fields:
            note = self.noi_nhan
        if note:
            parts.append(note)
        return parts

    @api.depends('loai_nguoi_nhan', 'khach_hang_id', 'khach_hang_nhan_ids', 'nhan_vien_nhan_ids', 'nguoi_nhan')
    def _compute_nguoi_nhan_phan_loai(self):
        for record in self:
            record.nguoi_nhan_phan_loai = '; '.join(record._get_nguoi_nhan_parts())

    @api.onchange('loai_nguoi_nhan')
    def _onchange_loai_nguoi_nhan_den(self):
        if self.loai_nguoi_nhan == 'khach_hang':
            self.nhan_vien_nhan_ids = [(5, 0, 0)]
        elif self.loai_nguoi_nhan == 'nhan_vien':
            self.khach_hang_id = False
            self.khach_hang_nhan_ids = [(5, 0, 0)]

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        if self.khach_hang_id and not self.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = self.khach_hang_id.nhan_vien_phu_trach_id

    @api.constrains('ngay_hieu_luc', 'ngay_het_han')
    def _check_ngay_hieu_luc(self):
        for record in self:
            if (
                record.ngay_hieu_luc
                and record.ngay_het_han
                and record.ngay_het_han < record.ngay_hieu_luc
            ):
                raise ValidationError("Ngày hết hạn không được nhỏ hơn ngày hiệu lực.")


class VanBanDi(models.Model):
    _inherit = 'van_ban_di'

    nhom_van_ban = fields.Selection(
        selection_add=[('khach_hang', 'Gửi khách hàng')],
        ondelete={'khach_hang': 'set default'},
    )
    khach_hang_id = fields.Many2one(
        'res.partner',
        string="Khách hàng",
        domain=[('is_khach_hang', '=', True)],
        index=True,
    )
    loai_nguoi_nhan = fields.Selection(
        RECIPIENT_TYPES,
        string="Loại người nhận",
        default='khach_hang',
        required=True,
    )
    nhan_vien_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên phụ trách",
    )
    nhom_ho_so = fields.Selection(
        DOCUMENT_GROUPS,
        string="Nhóm hồ sơ",
        default='khac',
        required=True,
    )
    ngay_hieu_luc = fields.Date(string="Ngày hiệu lực")
    ngay_het_han = fields.Date(string="Ngày hết hạn")
    trang_thai_ho_so = fields.Selection(
        DOCUMENT_STATES,
        string="Trạng thái hồ sơ",
        default='nhap',
        required=True,
    )
    tep_dinh_kem_ids = fields.Many2many(
        'ir.attachment',
        'van_ban_di_ir_attachment_rel',
        'van_ban_di_id',
        'attachment_id',
        string="Tệp đính kèm",
    )

    nguoi_nhan_phan_loai = fields.Char(
        string="Người nhận",
        compute='_compute_nguoi_nhan_phan_loai',
    )

    def _get_nguoi_nhan_parts(self):
        self.ensure_one()
        parts = []
        customer_names = []
        if self.khach_hang_id:
            customer_names.append(self.khach_hang_id.display_name)
        if 'khach_hang_nhan_ids' in self._fields:
            customer_names += [
                name for name in self.khach_hang_nhan_ids.mapped('display_name')
                if name not in customer_names
            ]
        parts += ["%s (khách hàng)" % name for name in customer_names]

        employee_names = []
        if 'nhan_vien_nhan_ids' in self._fields:
            employee_names = self.nhan_vien_nhan_ids.mapped('display_name')
        parts += ["%s (nhân viên)" % name for name in employee_names]

        note = self.noi_nhan if 'noi_nhan' in self._fields else False
        if note:
            parts.append(note)
        return parts

    @api.depends('loai_nguoi_nhan', 'khach_hang_id', 'khach_hang_nhan_ids', 'nhan_vien_nhan_ids', 'noi_nhan')
    def _compute_nguoi_nhan_phan_loai(self):
        for record in self:
            record.nguoi_nhan_phan_loai = '; '.join(record._get_nguoi_nhan_parts())

    @api.onchange('loai_nguoi_nhan')
    def _onchange_loai_nguoi_nhan_di(self):
        if self.loai_nguoi_nhan == 'khach_hang':
            self.nhom_van_ban = 'khach_hang'
            self.nhan_vien_nhan_ids = [(5, 0, 0)]
        elif self.loai_nguoi_nhan == 'nhan_vien':
            self.nhom_van_ban = 'nhan_vien'
            self.khach_hang_id = False
            self.khach_hang_nhan_ids = [(5, 0, 0)]

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        if self.khach_hang_id and not self.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = self.khach_hang_id.nhan_vien_phu_trach_id

    @api.constrains('ngay_hieu_luc', 'ngay_het_han')
    def _check_ngay_hieu_luc(self):
        for record in self:
            if (
                record.ngay_hieu_luc
                and record.ngay_het_han
                and record.ngay_het_han < record.ngay_hieu_luc
            ):
                raise ValidationError("Ngày hết hạn không được nhỏ hơn ngày hiệu lực.")
