from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Hồ sơ nhân viên'
    _rec_name = 'ho_ten'
    _order = 'ma_dinh_danh, ho_ten'

    active = fields.Boolean("Đang sử dụng", default=True)
    image_1920 = fields.Image("Ảnh nhân viên", max_width=1920, max_height=1920)
    ma_dinh_danh = fields.Char(
        "Mã nhân viên",
        required=True,
        copy=False,
        default='Mới',
        index=True,
    )
    ho_ten = fields.Char("Họ và tên", default="Chưa cập nhật", index=True)
    ten_khac = fields.Char("Tên gọi khác")
    gioi_tinh = fields.Selection([
        ('nam', 'Nam'),
        ('nu', 'Nữ'),
        ('khac', 'Khác'),
    ], string="Giới tính")
    ngay_sinh = fields.Date("Ngày sinh")
    tuoi = fields.Integer("Tuổi", compute='_compute_tuoi')
    noi_sinh = fields.Char("Nơi sinh")
    que_quan = fields.Char("Quê quán")
    quoc_tich = fields.Char("Quốc tịch", default="Việt Nam")
    dan_toc = fields.Char("Dân tộc")
    ton_giao = fields.Char("Tôn giáo")
    tinh_trang_hon_nhan = fields.Selection([
        ('doc_than', 'Độc thân'),
        ('ket_hon', 'Đã kết hôn'),
        ('ly_hon', 'Ly hôn'),
        ('khac', 'Khác'),
    ], string="Tình trạng hôn nhân", default='doc_than')

    so_cccd = fields.Char("Số CCCD/Hộ chiếu", index=True)
    ngay_cap_cccd = fields.Date("Ngày cấp")
    noi_cap_cccd = fields.Char("Nơi cấp")
    dia_chi_thuong_tru = fields.Text("Địa chỉ thường trú")
    dia_chi_tam_tru = fields.Text("Địa chỉ hiện tại")

    email = fields.Char("Email cá nhân")
    email_cong_ty = fields.Char("Email công ty")
    so_dien_thoai = fields.Char("Số điện thoại")
    nguoi_lien_he_khan_cap = fields.Char("Người liên hệ khẩn cấp")
    quan_he_khan_cap = fields.Char("Quan hệ")
    so_dien_thoai_khan_cap = fields.Char("SĐT khẩn cấp")

    phong_ban_id = fields.Many2one(
        'phong_ban',
        string="Phòng ban",
        ondelete='set null',
        index=True,
    )
    chuc_vu_id = fields.Many2one(
        'chuc_vu',
        string="Chức vụ",
        ondelete='set null',
        index=True,
    )
    quan_ly_id = fields.Many2one(
        'nhan_vien',
        string="Quản lý trực tiếp",
        ondelete='set null',
        domain="[('id', '!=', id)]",
    )
    cap_duoi_ids = fields.One2many('nhan_vien', 'quan_ly_id', string="Nhân viên cấp dưới")
    ngay_vao_lam = fields.Date("Ngày vào làm", default=fields.Date.context_today)
    ngay_nghi_viec = fields.Date("Ngày nghỉ việc")
    loai_nhan_vien = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('chinh_thuc', 'Chính thức'),
        ('thoi_vu', 'Thời vụ'),
        ('cong_tac_vien', 'Cộng tác viên'),
    ], string="Loại nhân viên", default='thu_viec', required=True)
    trang_thai = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('dang_lam', 'Đang làm việc'),
        ('tam_nghi', 'Tạm nghỉ'),
        ('da_nghi', 'Đã nghỉ việc'),
    ], string="Trạng thái", default='thu_viec', required=True, index=True)

    trinh_do_hoc_van = fields.Selection([
        ('thpt', 'Trung học phổ thông'),
        ('trung_cap', 'Trung cấp'),
        ('cao_dang', 'Cao đẳng'),
        ('dai_hoc', 'Đại học'),
        ('thac_si', 'Thạc sĩ'),
        ('tien_si', 'Tiến sĩ'),
        ('khac', 'Khác'),
    ], string="Trình độ học vấn")
    chuyen_nganh = fields.Char("Chuyên ngành")
    truong_dao_tao = fields.Char("Trường đào tạo")
    nam_tot_nghiep = fields.Integer("Năm tốt nghiệp")

    so_tai_khoan = fields.Char("Số tài khoản ngân hàng")
    ten_ngan_hang = fields.Char("Ngân hàng")
    chi_nhanh_ngan_hang = fields.Char("Chi nhánh")
    ma_so_thue = fields.Char("Mã số thuế cá nhân")
    so_bhxh = fields.Char("Số BHXH")
    so_bhyt = fields.Char("Số BHYT")

    hop_dong_ids = fields.One2many(
        'hop_dong_lao_dong',
        'nhan_vien_id',
        string="Hợp đồng lao động",
    )
    so_hop_dong = fields.Integer("Số hợp đồng", compute='_compute_so_hop_dong')

    nghi_phep_ids = fields.One2many('nghi_phep', 'nhan_vien_id', string="Nghỉ phép")
    dao_tao_bang_cap_ids = fields.One2many('dao_tao_bang_cap', 'nhan_vien_id', string="Đào tạo & Bằng cấp")
    danh_gia_ids = fields.One2many('danh_gia_nhan_vien', 'nhan_vien_id', string="Đánh giá")
    so_nghi_phep = fields.Integer("Số đơn nghỉ", compute='_compute_so_ho_so_mo_rong')
    so_dao_tao = fields.Integer("Số hồ sơ đào tạo", compute='_compute_so_ho_so_mo_rong')
    so_danh_gia = fields.Integer("Số đánh giá", compute='_compute_so_ho_so_mo_rong')
    ghi_chu = fields.Text("Ghi chú")

    @api.depends('ngay_sinh')
    def _compute_tuoi(self):
        today = fields.Date.context_today(self)
        for employee in self:
            if employee.ngay_sinh:
                birthday = employee.ngay_sinh
                employee.tuoi = (
                    today.year - birthday.year
                    - ((today.month, today.day) < (birthday.month, birthday.day))
                )
            else:
                employee.tuoi = 0

    @api.depends('hop_dong_ids')
    def _compute_so_hop_dong(self):
        for employee in self:
            employee.so_hop_dong = len(employee.hop_dong_ids)


    @api.depends('nghi_phep_ids', 'dao_tao_bang_cap_ids', 'danh_gia_ids')
    def _compute_so_ho_so_mo_rong(self):
        for employee in self:
            employee.so_nghi_phep = len(employee.nghi_phep_ids)
            employee.so_dao_tao = len(employee.dao_tao_bang_cap_ids)
            employee.so_danh_gia = len(employee.danh_gia_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ma_dinh_danh', 'Mới') == 'Mới':
                vals['ma_dinh_danh'] = self.env['ir.sequence'].next_by_code(
                    'nhan_vien.ma_dinh_danh'
                ) or 'Mới'
        return super().create(vals_list)

    def name_get(self):
        result = []
        for employee in self:
            name = employee.ho_ten or employee.ma_dinh_danh or "Nhân viên"
            if employee.ma_dinh_danh and employee.ho_ten:
                name = "[%s] %s" % (employee.ma_dinh_danh, employee.ho_ten)
            result.append((employee.id, name))
        return result

    @api.constrains('ma_dinh_danh')
    def _check_ma_dinh_danh_unique(self):
        for employee in self:
            if employee.ma_dinh_danh and self.search_count([
                ('ma_dinh_danh', '=', employee.ma_dinh_danh),
                ('id', '!=', employee.id),
            ]):
                raise ValidationError("Mã nhân viên đã tồn tại.")

    @api.constrains('ngay_sinh', 'ngay_vao_lam', 'ngay_nghi_viec')
    def _check_dates(self):
        today = fields.Date.context_today(self)
        for employee in self:
            if employee.ngay_sinh and employee.ngay_sinh > today:
                raise ValidationError("Ngày sinh không được lớn hơn ngày hiện tại.")
            if (
                employee.ngay_vao_lam
                and employee.ngay_nghi_viec
                and employee.ngay_nghi_viec < employee.ngay_vao_lam
            ):
                raise ValidationError("Ngày nghỉ việc phải sau ngày vào làm.")

    def action_thu_viec(self):
        self.write({'trang_thai': 'thu_viec', 'active': True})

    def action_dang_lam(self):
        self.write({'trang_thai': 'dang_lam', 'active': True})

    def action_tam_nghi(self):
        self.write({'trang_thai': 'tam_nghi'})

    def action_nghi_viec(self):
        self.write({
            'trang_thai': 'da_nghi',
            'ngay_nghi_viec': fields.Date.context_today(self),
        })

    def unlink(self):
        """Archive employees so linked business history remains intact."""
        self.write({
            'active': False,
            'trang_thai': 'da_nghi',
            'ngay_nghi_viec': fields.Date.context_today(self),
        })
        return True

    def action_view_hop_dong(self):
        self.ensure_one()
        action = self.env.ref('nhan_su.action_hop_dong_lao_dong').read()[0]
        action['domain'] = [('nhan_vien_id', '=', self.id)]
        action['context'] = {'default_nhan_vien_id': self.id}
        return action

    def action_view_nghi_phep(self):
        self.ensure_one()
        action = self.env.ref('nhan_su.action_nghi_phep').read()[0]
        action['domain'] = [('nhan_vien_id', '=', self.id)]
        action['context'] = {'default_nhan_vien_id': self.id}
        return action

    def action_view_dao_tao_bang_cap(self):
        self.ensure_one()
        action = self.env.ref('nhan_su.action_dao_tao_bang_cap').read()[0]
        action['domain'] = [('nhan_vien_id', '=', self.id)]
        action['context'] = {'default_nhan_vien_id': self.id}
        return action

    def action_view_danh_gia(self):
        self.ensure_one()
        action = self.env.ref('nhan_su.action_danh_gia_nhan_vien').read()[0]
        action['domain'] = [('nhan_vien_id', '=', self.id)]
        action['context'] = {'default_nhan_vien_id': self.id}
        return action
