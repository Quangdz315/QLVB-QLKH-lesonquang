from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    don_hang_ids = fields.One2many('qlkh.don_hang', 'khach_hang_id', string="Đơn hàng/Dịch vụ")
    thanh_toan_ids = fields.One2many('qlkh.thanh_toan', 'khach_hang_id', string="Thanh toán")
    so_don_hang = fields.Integer("Số đơn hàng", compute='_compute_sales_summary')
    tong_gia_tri_don_hang = fields.Float("Tổng giá trị đơn hàng", compute='_compute_sales_summary')
    tong_da_thanh_toan = fields.Float("Tổng đã thanh toán", compute='_compute_sales_summary')
    tong_cong_no = fields.Float("Tổng công nợ", compute='_compute_sales_summary')

    def _compute_sales_summary(self):
        for partner in self:
            orders = partner.don_hang_ids
            partner.so_don_hang = len(orders)
            partner.tong_gia_tri_don_hang = sum(orders.mapped('gia_tri'))
            partner.tong_da_thanh_toan = sum(orders.mapped('da_thanh_toan'))
            partner.tong_cong_no = sum(orders.mapped('con_no'))

    def action_view_don_hang(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_khach_hang_van_ban.action_qlkh_don_hang').read()[0]
        action['domain'] = [('khach_hang_id', '=', self.id)]
        action['context'] = {
            'default_khach_hang_id': self.id,
            'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
        }
        return action

    def action_view_thanh_toan(self):
        self.ensure_one()
        action = self.env.ref('quan_ly_khach_hang_van_ban.action_qlkh_thanh_toan').read()[0]
        action['domain'] = [('khach_hang_id', '=', self.id)]
        action['context'] = {'default_khach_hang_id': self.id}
        return action
