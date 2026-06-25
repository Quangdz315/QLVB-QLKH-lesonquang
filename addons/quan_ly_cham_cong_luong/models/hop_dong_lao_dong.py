from odoo import api, models


class HopDongLaoDong(models.Model):
    _inherit = 'hop_dong_lao_dong'

    def _dong_bo_cau_hinh_luong(self):
        SalaryConfig = self.env['hr_luong_co_ban']
        for contract in self:
            config = SalaryConfig.search([
                ('nhan_vien_id', '=', contract.nhan_vien_id.id),
            ], limit=1)
            vals = {
                'nhan_vien_id': contract.nhan_vien_id.id,
                'hop_dong_id': contract.id,
                'luong_co_ban': contract.luong_co_ban,
                'phu_cap_trach_nhiem': contract.phu_cap,
            }
            if config:
                config.write(vals)
            else:
                SalaryConfig.create(vals)
        return True

    def action_hieu_luc(self):
        result = super().action_hieu_luc()
        self._dong_bo_cau_hinh_luong()
        return result

    def action_dong_bo_cau_hinh_luong(self):
        self._dong_bo_cau_hinh_luong()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Đồng bộ thành công',
                'message': 'Lương và phụ cấp đã được đồng bộ từ hợp đồng.',
                'type': 'success',
                'sticky': False,
            },
        }

    def write(self, vals):
        result = super().write(vals)
        if {'luong_co_ban', 'phu_cap'} & set(vals) and self.filtered(
            lambda contract: contract.trang_thai == 'hieu_luc'
        ):
            self.filtered(
                lambda contract: contract.trang_thai == 'hieu_luc'
            )._dong_bo_cau_hinh_luong()
        return result
