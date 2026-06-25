from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qlvb_gemini_enabled = fields.Boolean(
        string='Su dung Google Gemini API',
        config_parameter='quan_ly_van_ban.gemini_enabled',
    )
    qlvb_gemini_api_key = fields.Char(
        string='Gemini API key',
        config_parameter='quan_ly_van_ban.gemini_api_key',
    )
    qlvb_gemini_model = fields.Char(
        string='Model Gemini',
        default='gemini-2.5-flash',
        config_parameter='quan_ly_van_ban.gemini_model',
    )
    qlvb_gemini_fallback = fields.Boolean(
        string='Dung AI noi bo khi API loi',
        default=True,
        config_parameter='quan_ly_van_ban.gemini_fallback',
    )

    def action_test_qlvb_gemini(self):
        self.ensure_one()
        self.set_values()
        self.env['quan_ly_van_ban.ai_gemini_service'].test_connection()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Ket noi thanh cong'),
                'message': _('Odoo da goi va nhan ket qua tu Google Gemini.'),
                'type': 'success',
                'sticky': False,
            },
        }
