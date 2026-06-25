from odoo import api, fields, models
from odoo.exceptions import UserError


class QlkhChamSoc(models.Model):
    _name = 'qlkh.cham_soc'
    _description = 'Chăm sóc khách hàng'
    _rec_name = 'name'
    _order = 'ngay_cham_soc desc, id desc'

    name = fields.Char("Mã chăm sóc", copy=False, readonly=True, default='Mới', index=True)
    khach_hang_id = fields.Many2one(
        'res.partner',
        string="Khách hàng",
        required=True,
        domain=[('is_khach_hang', '=', True)],
        ondelete='restrict',
        index=True,
    )
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    ngay_cham_soc = fields.Datetime(
        "Ngày chăm sóc",
        default=fields.Datetime.now,
        required=True,
    )
    kenh = fields.Selection([
        ('dien_thoai', 'Điện thoại'),
        ('email', 'Email'),
        ('zalo', 'Zalo'),
        ('sms', 'SMS'),
        ('gap_truc_tiep', 'Gặp trực tiếp'),
        ('khac', 'Khác'),
    ], string="Kênh liên hệ", default='zalo', required=True)
    muc_dich = fields.Selection([
        ('tu_van', 'Tư vấn'),
        ('nhac_cong_no', 'Nhắc công nợ'),
        ('gui_bao_gia', 'Gửi báo giá'),
        ('hoi_tham', 'Hỏi thăm'),
        ('xu_ly_khieu_nai', 'Xử lý khiếu nại'),
        ('khac', 'Khác'),
    ], string="Mục đích", default='hoi_tham', required=True)
    don_hang_id = fields.Many2one(
        'qlkh.don_hang',
        string="Đơn hàng/Dịch vụ liên quan",
        domain="[('khach_hang_id', '=', khach_hang_id)]",
    )
    noi_dung = fields.Text("Nội dung trao đổi")
    tin_nhan_goi_y = fields.Text("AI gợi ý tin nhắn")
    ket_qua = fields.Text("Kết quả")
    ngay_hen_tiep_theo = fields.Datetime("Ngày hẹn tiếp theo")
    trang_thai = fields.Selection([
        ('nhap', 'Bản nháp'),
        ('da_lien_he', 'Đã liên hệ'),
        ('can_goi_lai', 'Cần gọi lại'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, index=True)

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        if self.khach_hang_id and not self.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = self.khach_hang_id.nhan_vien_phu_trach_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Mới') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('qlkh.cham_soc') or 'Mới'
            if vals.get('khach_hang_id') and not vals.get('nhan_vien_phu_trach_id'):
                customer = self.env['res.partner'].browse(vals['khach_hang_id'])
                vals['nhan_vien_phu_trach_id'] = customer.nhan_vien_phu_trach_id.id
        return super().create(vals_list)

    def action_ai_goi_y_tin_nhan(self):
        service = self.env['quan_ly_van_ban.ai_gemini_service']
        for record in self:
            message = record._local_message_suggestion()
            if service.is_enabled():
                try:
                    answer = service.ask_assistant(
                        'Hay viet mot tin nhan cham soc khach hang ngan gon, lich su, de gui qua %s. Chi tra ve noi dung tin nhan.' % record.kenh,
                        'khach_hang',
                        record._prepare_ai_context(),
                    )
                except UserError:
                    if not service.fallback_enabled():
                        raise
                else:
                    if answer:
                        message = answer
            record.write({'tin_nhan_goi_y': message})
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chăm sóc khách hàng',
            'res_model': 'qlkh.cham_soc',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_da_lien_he(self):
        self.write({'trang_thai': 'da_lien_he'})

    def action_can_goi_lai(self):
        self.write({'trang_thai': 'can_goi_lai'})

    def action_hoan_thanh(self):
        self.write({'trang_thai': 'hoan_thanh'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})

    def action_dat_nhap(self):
        self.write({'trang_thai': 'nhap'})

    def _prepare_ai_context(self):
        self.ensure_one()
        customer = self.khach_hang_id
        lines = [
            "CHAM SOC KHACH HANG",
            "Khach hang: %s" % (customer.display_name or ''),
            "Ma khach hang: %s" % (customer.ma_khach_hang or ''),
            "Kenh lien he: %s" % (dict(self._fields['kenh'].selection).get(self.kenh) or self.kenh),
            "Muc dich: %s" % (dict(self._fields['muc_dich'].selection).get(self.muc_dich) or self.muc_dich),
            "Nhan vien phu trach: %s" % (self.nhan_vien_phu_trach_id.display_name or ''),
            "Trang thai cham soc KH: %s" % (customer.trang_thai_cham_soc or ''),
            "Muc uu tien KH: %s" % (customer.muc_do_uu_tien or ''),
            "Tong cong no: %.0f" % getattr(customer, 'tong_cong_no', 0.0),
            "So don hang: %s" % getattr(customer, 'so_don_hang', 0),
            "Noi dung trao doi hien tai: %s" % (self.noi_dung or ''),
        ]
        if self.don_hang_id:
            lines.append(
                "Don hang lien quan: %s | %s | gia tri=%.0f | con no=%.0f | trang thai=%s" % (
                    self.don_hang_id.ma_don_hang,
                    self.don_hang_id.ten_don_hang,
                    self.don_hang_id.gia_tri,
                    self.don_hang_id.con_no,
                    self.don_hang_id.trang_thai,
                )
            )
        for care in customer.cham_soc_ids[:5]:
            lines.append("- Lich su CS %s | %s | %s | %s" % (
                care.name,
                care.ngay_cham_soc or '',
                care.muc_dich or '',
                care.ket_qua or care.noi_dung or '',
            ))
        return "\n".join(lines)

    def _local_message_suggestion(self):
        self.ensure_one()
        customer_name = self.khach_hang_id.name or 'anh/chị'
        debt = getattr(self.khach_hang_id, 'tong_cong_no', 0.0)
        if self.muc_dich == 'nhac_cong_no':
            return (
                "Chào anh/chị %s, bên em xin phép nhắc công nợ hiện tại là %.0f. "
                "Anh/chị kiểm tra giúp em và phản hồi thời gian thanh toán dự kiến nhé. Em cảm ơn anh/chị."
            ) % (customer_name, debt)
        if self.muc_dich == 'gui_bao_gia':
            return (
                "Chào anh/chị %s, em gửi anh/chị thông tin báo giá/dịch vụ theo nhu cầu đã trao đổi. "
                "Anh/chị xem giúp em, nếu cần điều chỉnh em sẽ hỗ trợ ngay."
            ) % customer_name
        if self.muc_dich == 'xu_ly_khieu_nai':
            return (
                "Chào anh/chị %s, em đã ghi nhận vấn đề anh/chị phản ánh. "
                "Bên em sẽ kiểm tra và cập nhật hướng xử lý sớm nhất cho anh/chị."
            ) % customer_name
        return (
            "Chào anh/chị %s, em liên hệ để hỏi thăm và cập nhật nhu cầu hỗ trợ hiện tại. "
            "Nếu anh/chị cần tư vấn thêm về hồ sơ, văn bản hoặc dịch vụ, em sẵn sàng hỗ trợ."
        ) % customer_name


class ResPartnerCustomerCare(models.Model):
    _inherit = 'res.partner'

    cham_soc_ids = fields.One2many(
        'qlkh.cham_soc',
        'khach_hang_id',
        string="Lịch sử chăm sóc",
    )
    so_lan_cham_soc = fields.Integer(
        string="Số lần chăm sóc",
        compute='_compute_cham_soc_khach_hang',
    )
    ngay_cham_soc_gan_nhat = fields.Datetime(
        string="Chăm sóc gần nhất",
        compute='_compute_cham_soc_khach_hang',
    )
    ngay_hen_cham_soc_tiep_theo = fields.Datetime(
        string="Hẹn chăm sóc tiếp theo",
        compute='_compute_cham_soc_khach_hang',
    )

    def _compute_cham_soc_khach_hang(self):
        for partner in self:
            care_records = partner.cham_soc_ids.sorted(
                key=lambda care: care.ngay_cham_soc or fields.Datetime.now(),
                reverse=True,
            )
            partner.so_lan_cham_soc = len(care_records)
            partner.ngay_cham_soc_gan_nhat = care_records[:1].ngay_cham_soc if care_records else False
            upcoming = care_records.filtered(
                lambda care: care.ngay_hen_tiep_theo and care.trang_thai not in ('hoan_thanh', 'huy')
            ).sorted(key=lambda care: care.ngay_hen_tiep_theo)
            partner.ngay_hen_cham_soc_tiep_theo = upcoming[:1].ngay_hen_tiep_theo if upcoming else False

    def action_view_cham_soc(self):
        self.ensure_one()
        return {
            'name': 'Chăm sóc khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'qlkh.cham_soc',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {
                'default_khach_hang_id': self.id,
                'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
            },
        }
