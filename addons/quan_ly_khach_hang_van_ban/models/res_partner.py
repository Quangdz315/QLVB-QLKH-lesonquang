from collections import Counter

from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ma_khach_hang = fields.Char(
        string="Mã khách hàng",
        copy=False,
        index=True,
    )
    is_khach_hang = fields.Boolean(
        string="Là khách hàng",
        default=False,
        help="Đánh dấu đối tác được quản lý như hồ sơ khách hàng của đề tài 4.",
    )
    nhan_vien_phu_trach_id = fields.Many2one(
        'nhan_vien',
        string="Nhân viên phụ trách",
    )
    phan_loai_khach_hang = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp'),
        ('co_quan', 'Cơ quan/Tổ chức'),
    ], string="Phân loại", default='doanh_nghiep')
    muc_do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
    ], string="Mức độ ưu tiên", default='trung_binh')
    trang_thai_cham_soc = fields.Selection([
        ('moi', 'Mới'),
        ('dang_cham_soc', 'Đang chăm sóc'),
        ('da_ky_hop_dong', 'Đã ký hợp đồng'),
        ('tam_dung', 'Tạm dừng'),
    ], string="Trạng thái chăm sóc", default='moi')
    linh_vuc_hoat_dong = fields.Char(string="Lĩnh vực hoạt động")
    nguon_khach_hang = fields.Char(string="Nguồn khách hàng")
    ghi_chu_ho_so = fields.Text(string="Ghi chú hồ sơ")
    ai_phan_tich_luc = fields.Datetime(
        string="Thời điểm phân tích AI",
        readonly=True,
    )
    ai_nguon_phan_tich_ho_so = fields.Selection([
        ('noi_bo', 'AI nội bộ'),
        ('gemini', 'Google Gemini API'),
    ], string="Nguồn phân tích", readonly=True)
    ai_tom_tat_ho_so = fields.Text(
        string="AI tóm tắt hồ sơ",
        readonly=True,
    )
    ai_canh_bao = fields.Text(
        string="AI cảnh báo",
        readonly=True,
    )
    ai_goi_y_hanh_dong = fields.Text(
        string="AI gợi ý hành động",
        readonly=True,
    )
    ai_cham_soc_luc = fields.Datetime(
        string="Thời điểm AI chăm sóc",
        readonly=True,
    )
    ai_muc_do_cham_soc = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
    ], string="AI mức chăm sóc", readonly=True)
    ai_cham_soc_tom_tat = fields.Text(
        string="AI tóm tắt chăm sóc",
        readonly=True,
    )
    ai_kich_ban_lien_he = fields.Text(
        string="AI kịch bản liên hệ",
        readonly=True,
    )
    ai_cham_soc_hanh_dong = fields.Text(
        string="AI hành động chăm sóc",
        readonly=True,
    )

    van_ban_den_ids = fields.One2many(
        'van_ban_den',
        'khach_hang_id',
        string="Văn bản đến",
    )
    van_ban_di_ids = fields.One2many(
        'van_ban_di',
        'khach_hang_id',
        string="Văn bản đi",
    )
    so_van_ban_den = fields.Integer(
        string="Số văn bản đến",
        compute='_compute_so_luong_van_ban',
    )
    so_van_ban_di = fields.Integer(
        string="Số văn bản đi",
        compute='_compute_so_luong_van_ban',
    )
    tong_so_van_ban = fields.Integer(
        string="Tổng văn bản",
        compute='_compute_so_luong_van_ban',
    )

    _sql_constraints = [
        (
            'ma_khach_hang_unique',
            'unique(ma_khach_hang)',
            'Mã khách hàng đã tồn tại.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_khach_hang') and not vals.get('ma_khach_hang'):
                vals['ma_khach_hang'] = self._next_unique_customer_code()
        return super().create(vals_list)

    def _next_unique_customer_code(self):
        Partner = self.env['res.partner'].sudo()
        for _attempt in range(100):
            code = self.env['ir.sequence'].next_by_code('res.partner.khach_hang') or 'New'
            if not Partner.search_count([('ma_khach_hang', '=', code)]):
                return code
        return 'KH%s' % fields.Datetime.now().strftime('%Y%m%d%H%M%S')

    def _compute_so_luong_van_ban(self):
        VanBanDen = self.env['van_ban_den']
        VanBanDi = self.env['van_ban_di']
        for partner in self:
            partner.so_van_ban_den = VanBanDen.search_count([
                ('khach_hang_id', '=', partner.id),
            ])
            partner.so_van_ban_di = VanBanDi.search_count([
                ('khach_hang_id', '=', partner.id),
            ])
            partner.tong_so_van_ban = partner.so_van_ban_den + partner.so_van_ban_di

    def action_ai_phan_tich_ho_so(self):
        today = fields.Date.context_today(self)
        for partner in self:
            documents = list(partner.van_ban_den_ids) + list(partner.van_ban_di_ids)
            group_counter = Counter(doc.nhom_ho_so for doc in documents)
            state_counter = Counter(doc.trang_thai_ho_so for doc in documents)
            expired_docs = [
                doc for doc in documents
                if doc.ngay_het_han and doc.ngay_het_han < today
            ]
            expiring_docs = [
                doc for doc in documents
                if (
                    doc.ngay_het_han
                    and today <= doc.ngay_het_han
                    and (doc.ngay_het_han - today).days <= 30
                )
            ]

            partner.ai_phan_tich_luc = fields.Datetime.now()
            partner.ai_tom_tat_ho_so = partner._ai_build_summary(
                group_counter,
                state_counter,
            )
            partner.ai_canh_bao = partner._ai_build_warnings(
                documents,
                expired_docs,
                expiring_docs,
            )
            partner.ai_goi_y_hanh_dong = partner._ai_build_next_actions(
                documents,
                expired_docs,
                expiring_docs,
                group_counter,
            )
            partner.ai_nguon_phan_tich_ho_so = 'noi_bo'
            service = self.env['quan_ly_van_ban.ai_gemini_service']
            if service.is_enabled():
                try:
                    result = service.analyze_document(
                        partner._ai_customer_profile_text(documents), 'den',
                    )
                except UserError:
                    if not service.fallback_enabled():
                        raise
                else:
                    if result:
                        partner.ai_nguon_phan_tich_ho_so = 'gemini'
                        partner.ai_tom_tat_ho_so = result.get('summary') or partner.ai_tom_tat_ho_so
                        partner.ai_canh_bao = result.get('suggestion') or partner.ai_canh_bao
                        partner.ai_goi_y_hanh_dong = result.get('action') or partner.ai_goi_y_hanh_dong
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_ai_cham_soc_khach_hang(self):
        service = self.env['quan_ly_van_ban.ai_gemini_service']
        for partner in self:
            partner.ai_cham_soc_luc = fields.Datetime.now()
            values = partner._ai_customer_care_local_values()
            if service.is_enabled():
                try:
                    answer = service.ask_assistant(
                        'Hay lap ke hoach cham soc khach hang nay: tom tat tinh hinh, muc uu tien, kich ban lien he ngan gon va viec can lam tiep theo.',
                        'khach_hang',
                        partner._ai_customer_care_text(),
                    )
                except UserError:
                    if not service.fallback_enabled():
                        raise
                else:
                    if answer:
                        values['ai_cham_soc_tom_tat'] = answer
            partner.write(values)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _ai_customer_care_local_values(self):
        self.ensure_one()
        debt = getattr(self, 'tong_cong_no', 0.0)
        order_count = getattr(self, 'so_don_hang', 0)
        priority = self.muc_do_uu_tien or 'trung_binh'
        if debt > 0 or self.muc_do_uu_tien == 'cao':
            care_level = 'cao'
        elif order_count or self.trang_thai_cham_soc == 'dang_cham_soc':
            care_level = 'trung_binh'
        else:
            care_level = 'thap'

        summary = [
            "Khách hàng %s đang ở trạng thái %s, mức ưu tiên %s." % (
                self.display_name,
                dict(self._fields['trang_thai_cham_soc'].selection).get(
                    self.trang_thai_cham_soc, self.trang_thai_cham_soc,
                ),
                dict(self._fields['muc_do_uu_tien'].selection).get(priority, priority),
            ),
            "Hiện có %s đơn hàng/dịch vụ, tổng công nợ %.0f." % (order_count, debt),
            "Tổng văn bản liên quan: %s." % self.tong_so_van_ban,
        ]
        script = (
            "Chào anh/chị %s, em liên hệ để cập nhật tình hình hồ sơ và đơn hàng của mình. "
            "Bên em muốn xác nhận nhu cầu hiện tại, các vấn đề cần hỗ trợ và thống nhất bước xử lý tiếp theo."
        ) % (self.name or '')
        actions = []
        if debt > 0:
            actions.append("Nhắc lịch thanh toán/công nợ %.0f và thống nhất thời hạn xử lý." % debt)
        if not order_count:
            actions.append("Tư vấn dịch vụ phù hợp và tạo đơn hàng/dịch vụ đầu tiên.")
        if self.trang_thai_cham_soc == 'moi':
            actions.append("Gọi điện hoặc gửi email chào mừng, chuyển trạng thái sang đang chăm sóc.")
        if self.tong_so_van_ban:
            actions.append("Kiểm tra các văn bản liên quan trước khi trao đổi với khách hàng.")
        if not actions:
            actions.append("Duy trì liên hệ định kỳ, cập nhật nhu cầu mới và cơ hội bán thêm.")

        return {
            'ai_muc_do_cham_soc': care_level,
            'ai_cham_soc_tom_tat': "\n".join(summary),
            'ai_kich_ban_lien_he': script,
            'ai_cham_soc_hanh_dong': "\n".join("- %s" % action for action in actions),
        }

    def _ai_customer_care_text(self):
        self.ensure_one()
        lines = [
            "AI CHAM SOC KHACH HANG",
            "Khach hang: %s" % (self.display_name or ''),
            "Ma khach hang: %s" % (self.ma_khach_hang or ''),
            "Trang thai cham soc: %s" % (self.trang_thai_cham_soc or ''),
            "Muc uu tien: %s" % (self.muc_do_uu_tien or ''),
            "Nhan vien phu trach: %s" % (self.nhan_vien_phu_trach_id.display_name or ''),
            "Tong van ban: %s" % self.tong_so_van_ban,
            "So don hang: %s" % getattr(self, 'so_don_hang', 0),
            "Tong gia tri don hang: %.0f" % getattr(self, 'tong_gia_tri_don_hang', 0.0),
            "Tong da thanh toan: %.0f" % getattr(self, 'tong_da_thanh_toan', 0.0),
            "Tong cong no: %.0f" % getattr(self, 'tong_cong_no', 0.0),
            "So lan cham soc: %s" % getattr(self, 'so_lan_cham_soc', 0),
            "Cham soc gan nhat: %s" % (getattr(self, 'ngay_cham_soc_gan_nhat', False) or ''),
            "Hen cham soc tiep theo: %s" % (getattr(self, 'ngay_hen_cham_soc_tiep_theo', False) or ''),
            "Ghi chu ho so: %s" % (self.ghi_chu_ho_so or ''),
        ]
        if 'don_hang_ids' in self._fields:
            for order in self.don_hang_ids[:10]:
                lines.append("- Don hang %s | %s | gia tri=%.0f | con no=%.0f | trang thai=%s" % (
                    order.ma_don_hang,
                    order.ten_don_hang,
                    order.gia_tri,
                    order.con_no,
                    order.trang_thai,
                ))
        if 'thanh_toan_ids' in self._fields:
            for payment in self.thanh_toan_ids[:10]:
                lines.append("- Thanh toan %s | so tien=%.0f | trang thai=%s" % (
                    payment.name,
                    payment.so_tien,
                    payment.trang_thai,
                ))
        if 'cham_soc_ids' in self._fields:
            for care in self.cham_soc_ids[:10]:
                lines.append("- Cham soc %s | kenh=%s | muc dich=%s | trang thai=%s | hen=%s | ket qua=%s" % (
                    care.name,
                    care.kenh,
                    care.muc_dich,
                    care.trang_thai,
                    care.ngay_hen_tiep_theo or '',
                    care.ket_qua or care.noi_dung or '',
                ))
        return "\n".join(lines)

    def _ai_customer_profile_text(self, documents):
        self.ensure_one()
        lines = [
            "Phan tich HO SO KHACH HANG, khong phai mot van ban don le.",
            "Khach hang: %s" % (self.name or ''),
            "Ma: %s" % (self.ma_khach_hang or ''),
            "Linh vuc: %s" % (self.linh_vuc_hoat_dong or ''),
            "Trang thai cham soc: %s" % (self.trang_thai_cham_soc or ''),
            "Muc uu tien: %s" % (self.muc_do_uu_tien or ''),
            "Ghi chu: %s" % (self.ghi_chu_ho_so or ''),
            "Tong van ban: %s" % len(documents),
        ]
        for doc in documents[:30]:
            lines.append("- %s | nhom=%s | trang_thai=%s | het_han=%s" % (
                self._ai_get_document_name(doc), doc.nhom_ho_so or '',
                doc.trang_thai_ho_so or '', doc.ngay_het_han or '',
            ))
        return "\n".join(lines)

    def _ai_build_summary(self, group_counter, state_counter):
        self.ensure_one()
        summary = [
            "Khách hàng %s đang ở trạng thái %s, mức ưu tiên %s."
            % (
                self.name,
                dict(self._fields['trang_thai_cham_soc'].selection).get(
                    self.trang_thai_cham_soc,
                    self.trang_thai_cham_soc,
                ),
                dict(self._fields['muc_do_uu_tien'].selection).get(
                    self.muc_do_uu_tien,
                    self.muc_do_uu_tien,
                ),
            ),
            "Hồ sơ hiện có %s văn bản đến và %s văn bản đi."
            % (self.so_van_ban_den, self.so_van_ban_di),
        ]

        if self.nhan_vien_phu_trach_id:
            summary.append(
                "Nhân viên phụ trách: %s." % self.nhan_vien_phu_trach_id.display_name
            )
        if group_counter:
            group_labels = dict(self.env['van_ban_den']._fields['nhom_ho_so'].selection)
            summary.append(
                "Cơ cấu hồ sơ: %s."
                % ", ".join(
                    "%s: %s" % (group_labels.get(key, key), value)
                    for key, value in group_counter.items()
                )
            )
        if state_counter:
            state_labels = dict(self.env['van_ban_den']._fields['trang_thai_ho_so'].selection)
            summary.append(
                "Trạng thái xử lý: %s."
                % ", ".join(
                    "%s: %s" % (state_labels.get(key, key), value)
                    for key, value in state_counter.items()
                )
            )

        return "\n".join(summary)

    def _ai_build_warnings(self, documents, expired_docs, expiring_docs):
        warnings = []
        if not documents:
            warnings.append("Chưa có văn bản nào gắn với hồ sơ khách hàng.")
        if expired_docs:
            warnings.append(
                "Có %s văn bản đã hết hạn: %s."
                % (
                    len(expired_docs),
                    ", ".join(self._ai_get_document_name(doc) for doc in expired_docs[:5]),
                )
            )
        if expiring_docs:
            warnings.append(
                "Có %s văn bản sắp hết hạn trong 30 ngày: %s."
                % (
                    len(expiring_docs),
                    ", ".join(self._ai_get_document_name(doc) for doc in expiring_docs[:5]),
                )
            )
        missing_attachments = [doc for doc in documents if not doc.tep_dinh_kem_ids]
        if missing_attachments:
            warnings.append(
                "Có %s văn bản chưa có tệp đính kèm, cần bổ sung để hồ sơ số hóa đầy đủ."
                % len(missing_attachments)
            )

        return "\n".join(warnings) or "Chưa phát hiện rủi ro nổi bật trong hồ sơ."

    def _ai_build_next_actions(self, documents, expired_docs, expiring_docs, group_counter):
        actions = []
        if not documents:
            actions.append("Tạo ít nhất một báo giá, hợp đồng hoặc tài liệu pháp lý cho khách hàng.")
        if not group_counter.get('hop_dong'):
            actions.append("Kiểm tra khả năng chuyển đổi khách hàng sang hợp đồng chính thức.")
        if not group_counter.get('bao_gia'):
            actions.append("Chuẩn bị báo giá phù hợp với nhu cầu khách hàng.")
        if not group_counter.get('phap_ly'):
            actions.append("Bổ sung tài liệu pháp lý để hoàn thiện hồ sơ khách hàng.")
        if expired_docs or expiring_docs:
            actions.append("Liên hệ khách hàng để gia hạn hoặc cập nhật văn bản sắp hết hạn.")
        if self.muc_do_uu_tien == 'cao':
            actions.append("Ưu tiên chăm sóc khách hàng này trong kế hoạch làm việc gần nhất.")
        if self.trang_thai_cham_soc == 'moi':
            actions.append("Chuyển hồ sơ sang trạng thái đang chăm sóc sau khi có tương tác đầu tiên.")

        return "\n".join("- %s" % action for action in actions[:6])

    def _ai_get_document_name(self, document):
        return document.ten_van_ban or document.display_name or "Chưa đặt tên"

    def action_view_van_ban_den(self):
        self.ensure_one()
        return {
            'name': 'Văn bản đến của khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'van_ban_den',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }

    def action_view_van_ban_di(self):
        self.ensure_one()
        return {
            'name': 'Văn bản đi của khách hàng',
            'type': 'ir.actions.act_window',
            'res_model': 'van_ban_di',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id},
        }
