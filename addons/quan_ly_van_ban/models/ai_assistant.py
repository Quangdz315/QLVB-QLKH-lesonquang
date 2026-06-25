from odoo import api, fields, models
from odoo.exceptions import UserError


class QlvbAiAssistant(models.Model):
    _name = 'qlvb.ai_assistant'
    _description = 'AI Trợ lý'
    _order = 'write_date desc, id desc'

    name = fields.Char(string="Tiêu đề", default="Phiên hỏi AI", required=True)
    pham_vi = fields.Selection([
        ('tong_hop', 'Tổng hợp QLNS + QLVB + QLKH'),
        ('nhan_su', 'Quản lý nhân sự'),
        ('van_ban', 'Quản lý văn bản'),
        ('khach_hang', 'Quản lý khách hàng'),
    ], string="Phạm vi", default='tong_hop', required=True)
    cau_hoi = fields.Text(string="Câu hỏi", required=True)
    cau_tra_loi = fields.Text(string="Gemini trả lời", readonly=True)
    ngu_canh_du_lieu = fields.Text(string="Ngữ cảnh dữ liệu gửi AI", readonly=True)
    hoi_luc = fields.Datetime(string="Hỏi lúc", readonly=True)

    def action_hoi_gemini(self):
        service = self.env['quan_ly_van_ban.ai_gemini_service']
        if not service.is_enabled():
            raise UserError("Bạn cần bật Gemini và nhập API key ở QLVB > Cấu hình Gemini trước.")
        for record in self:
            context_text = record._build_business_context()
            answer = service.ask_assistant(record.cau_hoi, record.pham_vi, context_text)
            record.write({
                'cau_tra_loi': answer,
                'ngu_canh_du_lieu': context_text,
                'hoi_luc': fields.Datetime.now(),
            })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_lam_moi(self):
        self.write({
            'cau_hoi': False,
            'cau_tra_loi': False,
            'ngu_canh_du_lieu': False,
            'hoi_luc': False,
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def ask_from_widget(self, question, scope='tong_hop'):
        if not question:
            raise UserError("Bạn cần nhập câu hỏi cho trợ lý AI.")
        session = self.create({
            'name': 'Chat nhanh AI',
            'pham_vi': scope or 'tong_hop',
            'cau_hoi': question,
        })
        service = self.env['quan_ly_van_ban.ai_gemini_service']
        if not service.is_enabled():
            raise UserError("Bạn cần bật Gemini và nhập API key ở QLVB > Cấu hình Gemini trước.")
        context_text = session._build_business_context()
        answer = service.ask_assistant(question, session.pham_vi, context_text)
        session.write({
            'cau_tra_loi': answer,
            'ngu_canh_du_lieu': context_text,
            'hoi_luc': fields.Datetime.now(),
        })
        return {
            'answer': answer,
            'context': context_text,
            'session_id': session.id,
        }

    def _build_business_context(self):
        self.ensure_one()
        lines = []
        if self.pham_vi in ('tong_hop', 'nhan_su'):
            lines += self._context_nhan_su()
        if self.pham_vi in ('tong_hop', 'van_ban'):
            lines += self._context_van_ban()
        if self.pham_vi in ('tong_hop', 'khach_hang'):
            lines += self._context_khach_hang()
        return "\n".join(lines) or "Chua co du lieu ngu canh."

    def _context_nhan_su(self):
        env = self.env
        Employee = env['nhan_vien']
        lines = [
            "=== QLNS ===",
            "Tong nhan vien dang su dung: %s" % Employee.search_count([('active', '=', True)]),
            "Dang lam: %s" % Employee.search_count([('trang_thai', '=', 'dang_lam'), ('active', '=', True)]),
            "Thu viec: %s" % Employee.search_count([('trang_thai', '=', 'thu_viec'), ('active', '=', True)]),
            "Tam nghi: %s" % Employee.search_count([('trang_thai', '=', 'tam_nghi'), ('active', '=', True)]),
            "Hop dong lao dong: %s" % env['hop_dong_lao_dong'].search_count([]),
            "Don nghi phep cho duyet/nhap: %s" % env['nghi_phep'].search_count([('trang_thai', 'in', ['cho_duyet', 'nhap'])]),
        ]
        employees = Employee.search([('active', '=', True)], limit=8, order='id desc')
        for employee in employees:
            lines.append("- NV: %s | %s | %s | %s" % (
                employee.display_name,
                employee.phong_ban_id.display_name or 'Chua co phong ban',
                employee.chuc_vu_id.display_name or 'Chua co chuc vu',
                employee.trang_thai,
            ))
        return lines

    def _context_van_ban(self):
        env = self.env
        VanBanDen = env['van_ban_den']
        VanBanDi = env['van_ban_di']
        lines = [
            "=== QLVB ===",
            "Tong van ban den: %s" % VanBanDen.search_count([]),
            "Tong van ban di: %s" % VanBanDi.search_count([]),
            "Van ban den can xu ly gap theo AI: %s" % VanBanDen.search_count([('ai_can_xu_ly_gap', '=', True)]),
            "Van ban di can xu ly gap theo AI: %s" % VanBanDi.search_count([('ai_can_xu_ly_gap', '=', True)]),
        ]
        for doc in VanBanDen.search([], limit=6, order='id desc'):
            lines.append("- VB den: %s | %s | nguon=%s | AI=%s" % (
                doc.so_van_ban_den,
                doc.ten_van_ban,
                doc.nguon_gui_tong_hop or '',
                doc.ai_ket_qua_nhanh or '',
            ))
        for doc in VanBanDi.search([], limit=6, order='id desc'):
            lines.append("- VB di: %s | %s | nhan=%s | AI=%s" % (
                doc.so_van_ban_di,
                doc.ten_van_ban,
                doc.nguoi_nhan_tong_hop or '',
                doc.ai_ket_qua_nhanh or '',
            ))
        return lines

    def _context_khach_hang(self):
        Partner = self.env['res.partner']
        if 'is_khach_hang' not in Partner._fields:
            return ["=== QLKH ===", "Module QLKH chua cai dat hoac chua co field is_khach_hang."]
        try:
            Order = self.env['qlkh.don_hang']
        except KeyError:
            Order = False
        try:
            Payment = self.env['qlkh.thanh_toan']
        except KeyError:
            Payment = False
        try:
            Care = self.env['qlkh.cham_soc']
        except KeyError:
            Care = False
        has_order = Order is not False
        has_payment = Payment is not False
        has_care = Care is not False
        orders = Order.search([]) if has_order else False
        confirmed_payments = Payment.search([('trang_thai', '=', 'xac_nhan')]) if has_payment else False
        care_records = Care.search([]) if has_care else False
        total_order_value = sum(orders.mapped('gia_tri')) if orders else 0.0
        total_paid = sum(confirmed_payments.mapped('so_tien')) if confirmed_payments else 0.0
        total_debt = sum(orders.mapped('con_no')) if orders else 0.0
        lines = [
            "=== QLKH ===",
            "Tong khach hang: %s" % Partner.search_count([('is_khach_hang', '=', True)]),
            "Khach hang uu tien cao: %s" % Partner.search_count([('is_khach_hang', '=', True), ('muc_do_uu_tien', '=', 'cao')]),
            "Dang cham soc: %s" % Partner.search_count([('is_khach_hang', '=', True), ('trang_thai_cham_soc', '=', 'dang_cham_soc')]),
            "Da ky hop dong: %s" % Partner.search_count([('is_khach_hang', '=', True), ('trang_thai_cham_soc', '=', 'da_ky_hop_dong')]),
            "Tong don hang/dich vu: %s" % (Order.search_count([]) if has_order else 0),
            "Don hang dang thuc hien: %s" % (Order.search_count([('trang_thai', '=', 'dang_thuc_hien')]) if has_order else 0),
            "Don hang con cong no: %s" % (Order.search_count([('con_no', '>', 0)]) if has_order else 0),
            "Tong gia tri don hang: %.0f" % total_order_value,
            "Tong da thanh toan: %.0f" % total_paid,
            "Tong cong no: %.0f" % total_debt,
            "Tong lan cham soc khach hang: %s" % (Care.search_count([]) if has_care else 0),
            "Cham soc can goi lai: %s" % (Care.search_count([('trang_thai', '=', 'can_goi_lai')]) if has_care else 0),
            "Cham soc nhac cong no: %s" % (Care.search_count([('muc_dich', '=', 'nhac_cong_no')]) if has_care else 0),
        ]
        customers = Partner.search([('is_khach_hang', '=', True)], limit=8, order='id desc')
        for customer in customers:
            lines.append("- KH: %s | ma=%s | phu trach=%s | trang thai=%s | tong VB=%s | don hang=%s | cong no=%.0f" % (
                customer.display_name,
                customer.ma_khach_hang or '',
                customer.nhan_vien_phu_trach_id.display_name or 'Chua phan cong',
                customer.trang_thai_cham_soc or '',
                customer.tong_so_van_ban,
                getattr(customer, 'so_don_hang', 0),
                getattr(customer, 'tong_cong_no', 0.0),
            ))
        if has_order:
            lines.append("=== DON HANG/DICH VU GAN DAY ===")
            for order in Order.search([], limit=8, order='id desc'):
                lines.append("- DH: %s | %s | KH=%s | gia tri=%.0f | da TT=%.0f | con no=%.0f | trang thai=%s" % (
                    order.ma_don_hang,
                    order.ten_don_hang,
                    order.khach_hang_id.display_name or '',
                    order.gia_tri,
                    order.da_thanh_toan,
                    order.con_no,
                    order.trang_thai,
                ))
        if has_payment:
            lines.append("=== THANH TOAN GAN DAY ===")
            for payment in Payment.search([], limit=8, order='id desc'):
                lines.append("- TT: %s | KH=%s | DH=%s | so tien=%.0f | phuong thuc=%s | trang thai=%s" % (
                    payment.name,
                    payment.khach_hang_id.display_name or '',
                    payment.don_hang_id.ma_don_hang or '',
                    payment.so_tien,
                    payment.phuong_thuc,
                    payment.trang_thai,
                ))
        if has_care:
            lines.append("=== CHAM SOC KHACH HANG GAN DAY ===")
            for care in care_records[:8]:
                lines.append("- CS: %s | KH=%s | kenh=%s | muc dich=%s | hen tiep=%s | trang thai=%s | ket qua=%s" % (
                    care.name,
                    care.khach_hang_id.display_name or '',
                    care.kenh,
                    care.muc_dich,
                    care.ngay_hen_tiep_theo or '',
                    care.trang_thai,
                    care.ket_qua or care.noi_dung or '',
                ))
        return lines
