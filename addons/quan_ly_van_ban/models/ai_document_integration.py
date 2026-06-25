from odoo import api, fields, models
from odoo.exceptions import UserError


class CloudAIDocumentMixin(models.AbstractModel):
    _name = 'quan_ly_van_ban.openai_document_mixin'
    _description = 'Google Gemini integration helpers'

    ai_nguon_phan_tich = fields.Selection([
        ('noi_bo', 'AI noi bo'),
        ('gemini', 'Google Gemini API'),
    ], string='Nguon AI', readonly=True)

    def _prepare_gemini_values(self, direction):
        self.ensure_one()
        local_values = self._prepare_ai_values()
        local_values['ai_nguon_phan_tich'] = 'noi_bo'
        service = self.env['quan_ly_van_ban.ai_gemini_service']
        if not self.env.context.get('use_gemini') or not service.is_enabled():
            return local_values
        try:
            data = service.analyze_document(self._ai_text(), direction)
        except UserError:
            if service.fallback_enabled():
                return local_values
            raise
        if not data:
            return local_values

        group = data.get('group', 'chung')
        group_label = dict(self._fields['nhom_van_ban'].selection).get(group, group)
        priority = data.get('priority', 'trung_binh')
        values = {
            'ai_tom_tat': data.get('summary') or local_values['ai_tom_tat'],
            'ai_muc_do_uu_tien': priority,
            'ai_can_xu_ly_gap': priority == 'cao',
            'ai_ket_qua_nhanh': '%s - %s' % (
                data.get('quick_result') or 'Da phan tich',
                group_label,
            ),
            'ai_hanh_dong_de_xuat': data.get('action') or local_values['ai_hanh_dong_de_xuat'],
            'ai_goi_y': data.get('suggestion') or local_values['ai_goi_y'],
            'ai_da_phan_tich_luc': fields.Datetime.now(),
            'ai_nguon_phan_tich': 'gemini',
            'nhom_van_ban': group,
        }
        document_type = (data.get('document_type') or '').strip()
        if document_type:
            loai = self.env['loai_van_ban'].search([('name', 'ilike', document_type)], limit=1)
            if loai:
                values['loai_van_ban_id'] = loai.id
        return values

    def _ensure_ai_saved(self):
        for record in self:
            if record.ai_nguon_phan_tich == 'gemini':
                continue
            if record.noi_dung_ai or record.ten_van_ban:
                values = record._prepare_ai_values()
                values['ai_nguon_phan_tich'] = 'noi_bo'
                record.with_context(skip_auto_ai=True).write(values)


class VanBanDenGemini(models.Model):
    _name = 'van_ban_den'
    _inherit = ['van_ban_den', 'quan_ly_van_ban.openai_document_mixin']

    @api.onchange('ten_van_ban', 'so_hieu_van_ban', 'noi_dung_ai', 'ai_chay_ngay')
    def _onchange_ai_phan_tich_nhanh(self):
        for record in self:
            if record.ten_van_ban or record.so_hieu_van_ban or record.noi_dung_ai or record.ai_chay_ngay:
                values = record.with_context(use_gemini=bool(record.ai_chay_ngay))._prepare_gemini_values('den')
                for field_name, value in values.items():
                    record[field_name] = value
                record.ai_chay_ngay = False

    def action_ai_phan_tich(self):
        for record in self:
            values = record.with_context(use_gemini=True)._prepare_gemini_values('den')
            record.with_context(skip_auto_ai=True).write(values)
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class VanBanDiGemini(models.Model):
    _name = 'van_ban_di'
    _inherit = ['van_ban_di', 'quan_ly_van_ban.openai_document_mixin']

    @api.onchange('ten_van_ban', 'so_hieu_van_ban', 'noi_dung_ai', 'ai_chay_ngay')
    def _onchange_ai_phan_tich_nhanh(self):
        for record in self:
            if record.ten_van_ban or record.so_hieu_van_ban or record.noi_dung_ai or record.ai_chay_ngay:
                values = record.with_context(use_gemini=bool(record.ai_chay_ngay))._prepare_gemini_values('di')
                for field_name, value in values.items():
                    record[field_name] = value
                record.ai_chay_ngay = False

    def action_ai_phan_tich(self):
        for record in self:
            values = record.with_context(use_gemini=True)._prepare_gemini_values('di')
            record.with_context(skip_auto_ai=True).write(values)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
