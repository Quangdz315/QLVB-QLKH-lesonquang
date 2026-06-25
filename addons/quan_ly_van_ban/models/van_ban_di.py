from odoo import api, fields, models


class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Văn bản đi'
    _rec_name = 'ten_van_ban'

    so_van_ban_di = fields.Char(string="Số văn bản đi", required=True)
    so_hieu_van_ban = fields.Char(string="Số hiệu văn bản")
    ten_van_ban = fields.Char(string="Tên văn bản")

    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản")
    nhom_van_ban = fields.Selection([
        ('nhan_vien', 'Gửi cho nhân viên'),
        ('phong_ban', 'Gửi cho phòng ban'),
        ('noi_bo', 'Văn bản nội bộ'),
        ('co_quan_doi_tac', 'Gửi cơ quan/đối tác'),
        ('chung', 'Văn bản chung'),
    ], string="Nhóm văn bản", default='chung', required=True, index=True)

    don_vi_soan_thao = fields.Char(string="Đơn vị soạn thảo")
    nguoi_ky = fields.Char(string="Người ký")
    noi_nhan = fields.Text(string="Ghi chú nơi nhận")

    nhan_vien_nhan_ids = fields.Many2many(
        'nhan_vien',
        'van_ban_di_nhan_vien_rel',
        'van_ban_di_id',
        'nhan_vien_id',
        string="Nhân viên nhận",
    )
    phong_ban_nhan_ids = fields.Many2many(
        'phong_ban',
        'van_ban_di_phong_ban_rel',
        'van_ban_di_id',
        'phong_ban_id',
        string="Phòng ban nhận",
    )
    co_quan_doi_tac_nhan_ids = fields.Many2many(
        'res.partner',
        'van_ban_di_doi_tac_rel',
        'van_ban_di_id',
        'partner_id',
        string="Cơ quan/Đối tác nhận",
    )

    # Kept for customer-document module compatibility. Hidden from the generic QLVB views.
    khach_hang_nhan_ids = fields.Many2many(
        'res.partner',
        'van_ban_di_res_partner_rel',
        'van_ban_di_id',
        'partner_id',
        string="Khách hàng nhận",
    )

    nguoi_nhan_tong_hop = fields.Char(
        string="Người nhận",
        compute='_compute_nguoi_nhan_tong_hop',
    )
    noi_dung_ai = fields.Text(string="Nội dung AI phân tích")
    ai_chay_ngay = fields.Boolean(string="Chạy AI ngay")
    ai_tom_tat = fields.Text(string="AI tóm tắt", readonly=True)
    ai_goi_y = fields.Text(string="AI gợi ý xử lý", readonly=True)
    ai_muc_do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
    ], string="AI mức ưu tiên", readonly=True)
    ai_da_phan_tich_luc = fields.Datetime(string="AI phân tích lúc", readonly=True)
    ai_ket_qua_nhanh = fields.Char(string="Kết quả AI", readonly=True)
    ai_can_xu_ly_gap = fields.Boolean(string="AI cảnh báo xử lý gấp", readonly=True)
    ai_hanh_dong_de_xuat = fields.Char(string="AI hành động đề xuất", readonly=True)

    @api.depends(
        'nhom_van_ban',
        'nhan_vien_nhan_ids',
        'phong_ban_nhan_ids',
        'co_quan_doi_tac_nhan_ids',
        'khach_hang_nhan_ids',
        'noi_nhan',
    )
    def _compute_nguoi_nhan_tong_hop(self):
        for record in self:
            parts = []
            parts += [
                "%s (nhân viên)" % name
                for name in record.nhan_vien_nhan_ids.mapped('display_name')
            ]
            parts += [
                "%s (phòng ban)" % name
                for name in record.phong_ban_nhan_ids.mapped('display_name')
            ]
            parts += [
                "%s (cơ quan/đối tác)" % name
                for name in record.co_quan_doi_tac_nhan_ids.mapped('display_name')
            ]
            parts += [
                "%s (khách hàng)" % name
                for name in record.khach_hang_nhan_ids.mapped('display_name')
                if name not in record.co_quan_doi_tac_nhan_ids.mapped('display_name')
            ]
            if record.nhom_van_ban == 'noi_bo' and not parts:
                parts.append('Nội bộ')
            if record.nhom_van_ban == 'chung' and not parts:
                parts.append('Văn bản chung')
            if record.noi_nhan:
                parts.append(record.noi_nhan)
            record.nguoi_nhan_tong_hop = '; '.join(parts)

    def _ai_text(self):
        self.ensure_one()
        values = [
            self.ten_van_ban,
            self.so_hieu_van_ban,
            self.noi_dung_ai,
            self.noi_nhan,
            self.nguoi_nhan_tong_hop,
            self.don_vi_soan_thao,
            self.nguoi_ky,
        ]
        return ' '.join(value for value in values if value)

    def _ai_priority(self, text_lower):
        high_words = ['khẩn', 'gấp', 'ngay', 'hỏa tốc', 'khiếu nại', 'vi phạm', 'phạt', 'kiện', 'hết hạn']
        medium_words = ['hợp đồng', 'thanh toán', 'báo giá', 'phê duyệt', 'xác nhận', 'đàm phán']
        if any(word in text_lower for word in high_words):
            return 'cao'
        if any(word in text_lower for word in medium_words):
            return 'trung_binh'
        return 'thap'

    def _ai_group(self, text_lower):
        if any(word in text_lower for word in ['nhân viên', 'cán bộ', 'người lao động']):
            return 'nhan_vien'
        if any(word in text_lower for word in ['phòng ban', 'bộ phận', 'khoa ']):
            return 'phong_ban'
        if any(word in text_lower for word in ['đối tác', 'công ty', 'doanh nghiệp', 'cơ quan', 'khách hàng']):
            return 'co_quan_doi_tac'
        if any(word in text_lower for word in ['nội bộ', 'quy định', 'thông báo nội bộ']):
            return 'noi_bo'
        return 'chung'

    def _ai_type_keyword(self, text_lower):
        for keyword in ['hợp đồng', 'báo giá', 'thanh toán', 'quyết định', 'thông báo', 'công văn', 'biên bản', 'đề nghị', 'pháp lý']:
            if keyword in text_lower:
                return keyword
        return False

    def _ai_summary(self, text):
        clean = ' '.join(text.split())
        if not clean:
            return 'Chưa có đủ dữ liệu để tóm tắt. Hãy nhập tên văn bản hoặc nội dung AI phân tích.'
        if len(clean) <= 220:
            return clean
        return clean[:220].rsplit(' ', 1)[0] + '...'

    def _prepare_ai_values(self):
        self.ensure_one()
        text = self._ai_text()
        text_lower = text.lower()
        group = self._ai_group(text_lower)
        priority = self._ai_priority(text_lower)
        type_keyword = self._ai_type_keyword(text_lower)
        loai = False
        if type_keyword:
            loai = self.env['loai_van_ban'].search([('name', 'ilike', type_keyword)], limit=1)
        priority_label = dict(self._fields['ai_muc_do_uu_tien'].selection).get(priority, priority)
        group_label = dict(self._fields['nhom_van_ban'].selection).get(group, group)
        if priority == 'cao':
            quick_result = 'Cần xử lý gấp'
            action = 'Giao người phụ trách xử lý ngay trong ngày và theo dõi phản hồi.'
        elif priority == 'trung_binh':
            quick_result = 'Theo dõi'
            action = 'Đưa vào danh sách theo dõi, hẹn kiểm tra lại trong 2-3 ngày.'
        else:
            quick_result = 'Lưu hồ sơ'
            action = 'Lưu hồ sơ, chưa cần ưu tiên xử lý.'
        vals = {
            'ai_tom_tat': self._ai_summary(text),
            'ai_muc_do_uu_tien': priority,
            'ai_can_xu_ly_gap': priority == 'cao',
            'ai_ket_qua_nhanh': '%s - %s' % (quick_result, group_label),
            'ai_hanh_dong_de_xuat': action,
            'ai_goi_y': 'Kết luận: %s. Nhóm phù hợp: %s. Mức ưu tiên: %s.%s' % (
                quick_result,
                group_label,
                priority_label,
                ' Loại văn bản gợi ý: %s.' % loai.name if loai else ' Chưa tìm thấy loại văn bản trùng từ khóa.'
            ),
            'ai_da_phan_tich_luc': fields.Datetime.now(),
            'nhom_van_ban': group,
        }
        if loai:
            vals['loai_van_ban_id'] = loai.id
        return vals

    @api.onchange('ten_van_ban', 'so_hieu_van_ban', 'noi_dung_ai', 'ai_chay_ngay')
    def _onchange_ai_phan_tich_nhanh(self):
        for record in self:
            if record.ten_van_ban or record.so_hieu_van_ban or record.noi_dung_ai or record.ai_chay_ngay:
                for field_name, value in record._prepare_ai_values().items():
                    record[field_name] = value
                record.ai_chay_ngay = False

    def action_ai_phan_tich(self):
        for record in self:
            record.write(record._prepare_ai_values())
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def _ensure_ai_saved(self):
        for record in self:
            if record.noi_dung_ai or record.ten_van_ban:
                record.with_context(skip_auto_ai=True).write(record._prepare_ai_values())

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_auto_ai'):
            records._ensure_ai_saved()
        return records

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_auto_ai') and any(
            name in vals for name in ['ten_van_ban', 'so_hieu_van_ban', 'noi_dung_ai']
        ):
            self._ensure_ai_saved()
        return result
