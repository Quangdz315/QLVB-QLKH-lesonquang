from odoo import models, fields

class LoaiVanBan(models.Model):
    _name = 'loai_van_ban'
    _description = 'Loại văn bản'

    name = fields.Char(string="Tên loại", required=True)