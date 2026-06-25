import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

from odoo import _, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class AiGeminiService(models.AbstractModel):
    _name = 'quan_ly_van_ban.ai_gemini_service'
    _description = 'Google Gemini service for document management'

    def _config(self):
        params = self.env['ir.config_parameter'].sudo()
        env_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        env_model = os.getenv('GEMINI_MODEL')
        return {
            'enabled': (
                params.get_param('quan_ly_van_ban.gemini_enabled') == 'True'
                or bool(env_api_key)
            ),
            'api_key': params.get_param('quan_ly_van_ban.gemini_api_key') or env_api_key,
            'model': params.get_param('quan_ly_van_ban.gemini_model') or env_model or 'gemini-2.5-flash',
            'fallback': params.get_param('quan_ly_van_ban.gemini_fallback', 'True') == 'True',
        }

    def is_enabled(self):
        config = self._config()
        return bool(config['enabled'] and config['api_key'])

    def fallback_enabled(self):
        return self._config()['fallback']

    def _parse_json(self, text):
        clean = (text or '').strip()
        fence = chr(96) * 3
        if clean.startswith(fence):
            clean = clean.split('\n', 1)[-1]
            clean = clean.rsplit(fence, 1)[0].strip()
        try:
            return json.loads(clean)
        except (TypeError, ValueError):
            start = clean.find('{')
            end = clean.rfind('}')
            if start >= 0 and end > start:
                try:
                    return json.loads(clean[start:end + 1])
                except ValueError:
                    pass
        raise UserError(_('Gemini khong tra ve du lieu JSON hop le.'))

    def _prompt(self, text, direction):
        direction_label = 'van ban den' if direction == 'den' else 'van ban di'
        return (
            'Ban la tro ly van thu tieng Viet. Hay phan tich %s duoi day.\n'
            'Chi tra ve mot JSON object gom dung cac khoa:\n'
            'summary: tom tat ngan gon bang tieng Viet;\n'
            'priority: mot trong thap, trung_binh, cao;\n'
            'group: mot trong nhan_vien, phong_ban, noi_bo, co_quan_doi_tac, chung;\n'
            'quick_result: ket luan ngan;\n'
            'suggestion: ly do va goi y xu ly;\n'
            'action: hanh dong cu the;\n'
            'document_type: loai van ban ngan gon hoac chuoi rong.\n\n'
            'Noi dung:\n%s'
        ) % (direction_label, text or '')

    def ask_assistant(self, question, scope, context_text):
        config = self._config()
        if not config['enabled'] or not config['api_key']:
            return False

        scope_label = {
            'tong_hop': 'tong hop QLNS, QLVB va QLKH',
            'nhan_su': 'quan ly nhan su',
            'van_ban': 'quan ly van ban',
            'khach_hang': 'quan ly khach hang',
        }.get(scope, 'tong hop')
        prompt = (
            'Ban la tro ly AI trong he thong Odoo tieng Viet. '
            'Hay tra loi ngan gon, ro rang, uu tien hanh dong cu the. '
            'Neu cau hoi can du lieu ma ngu canh khong co, hay noi ro chua du du lieu.\n\n'
            'Pham vi: %s\n'
            'Ngu canh du lieu trong he thong:\n%s\n\n'
            'Cau hoi nguoi dung:\n%s'
        ) % (scope_label, context_text or 'Khong co ngu canh.', question or '')

        model = urllib.parse.quote(config['model'], safe='-_.')
        endpoint = (
            'https://generativelanguage.googleapis.com/v1beta/models/'
            '%s:generateContent' % model
        )
        payload = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.35,
            },
        }).encode('utf-8')
        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                'x-goog-api-key': config['api_key'],
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            _logger.warning('Gemini assistant HTTP %s: %s', exc.code, detail[:500])
            if exc.code == 429:
                message = _('Gemini da vuot han muc mien phi hoac dang bi gioi han tan suat.')
            elif exc.code in (401, 403):
                message = _('Gemini API key khong hop le hoac chua duoc cap quyen.')
            elif exc.code == 404:
                message = _('Khong tim thay model Gemini. Hay kiem tra ten model trong cau hinh.')
            else:
                message = _('Gemini tu choi yeu cau (HTTP %s).') % exc.code
            raise UserError(message)
        except (urllib.error.URLError, TimeoutError) as exc:
            _logger.warning('Gemini assistant connection error: %s', exc)
            raise UserError(_('Khong ket noi duoc Google Gemini. Kiem tra mang may chu Odoo.'))

        try:
            parts = result['candidates'][0]['content']['parts']
            return '\n'.join(part.get('text', '') for part in parts).strip()
        except (KeyError, IndexError, TypeError):
            _logger.warning('Unexpected Gemini assistant response: %s', str(result)[:500])
            raise UserError(_('Gemini khong tra ve cau tra loi.'))


    def analyze_document(self, text, direction):
        config = self._config()
        if not config['enabled'] or not config['api_key']:
            return False

        model = urllib.parse.quote(config['model'], safe='-_.')
        endpoint = (
            'https://generativelanguage.googleapis.com/v1beta/models/'
            '%s:generateContent' % model
        )
        payload = json.dumps({
            'contents': [{'parts': [{'text': self._prompt(text, direction)}]}],
            'generationConfig': {
                'responseMimeType': 'application/json',
                'temperature': 0.2,
            },
        }).encode('utf-8')
        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                'x-goog-api-key': config['api_key'],
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            _logger.warning('Gemini HTTP %s: %s', exc.code, detail[:500])
            if exc.code == 429:
                message = _('Gemini da vuot han muc mien phi hoac dang bi gioi han tan suat.')
            elif exc.code in (401, 403):
                message = _('Gemini API key khong hop le hoac chua duoc cap quyen.')
            elif exc.code == 404:
                message = _('Khong tim thay model Gemini. Hay kiem tra ten model trong cau hinh.')
            else:
                message = _('Gemini tu choi yeu cau (HTTP %s).') % exc.code
            raise UserError(message)
        except (urllib.error.URLError, TimeoutError) as exc:
            _logger.warning('Gemini connection error: %s', exc)
            raise UserError(_('Khong ket noi duoc Google Gemini. Kiem tra mang may chu Odoo.'))

        try:
            parts = result['candidates'][0]['content']['parts']
            output_text = '\n'.join(part.get('text', '') for part in parts).strip()
        except (KeyError, IndexError, TypeError):
            _logger.warning('Unexpected Gemini response: %s', str(result)[:500])
            raise UserError(_('Gemini khong tra ve noi dung phan tich.'))

        data = self._parse_json(output_text)
        if data.get('priority') not in ('thap', 'trung_binh', 'cao'):
            data['priority'] = 'trung_binh'
        if data.get('group') not in ('nhan_vien', 'phong_ban', 'noi_bo', 'co_quan_doi_tac', 'chung'):
            data['group'] = 'chung'
        return data

    def test_connection(self):
        result = self.analyze_document('Thong bao hop noi bo luc 9 gio sang mai.', 'den')
        if not result:
            raise UserError(_('Hay bat Gemini va nhap API key truoc khi kiem tra.'))
        return result
