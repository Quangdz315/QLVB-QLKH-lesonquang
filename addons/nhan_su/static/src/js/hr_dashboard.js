odoo.define('nhan_su.hr_dashboard', function (require) {
    'use strict';

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const QWeb = core.qweb;

    const HrDashboard = AbstractAction.extend({
        template: 'nhan_su.HrDashboard',

        events: {
            'click .o_ql_dashboard_card': '_onOpenAction',
            'click .o_ql_dash_link': '_onOpenAction',
        },

        init: function () {
            this._super.apply(this, arguments);
            this.data = {
                stats: [],
                departments: [],
                recentEmployees: [],
                contracts: [],
                candidates: [],
                statusBars: [],
            };
        },

        willStart: function () {
            return Promise.all([this._super.apply(this, arguments), this._loadData()]);
        },

        start: function () {
            this.$el.html(QWeb.render('nhan_su.HrDashboardContent', { data: this.data }));
            return this._super.apply(this, arguments);
        },

        _count: function (model, domain) {
            return this._rpc({ model: model, method: 'search_count', args: [domain || []] });
        },

        _read: function (model, domain, fields, limit, order) {
            return this._rpc({
                model: model,
                method: 'search_read',
                args: [domain || [], fields, 0, limit || 5, order || 'id desc'],
            });
        },

        _loadData: async function () {
            const total = await this._count('nhan_vien', [['active', '=', true]]);
            const working = await this._count('nhan_vien', [['trang_thai', '=', 'dang_lam'], ['active', '=', true]]);
            const probation = await this._count('nhan_vien', [['trang_thai', '=', 'thu_viec'], ['active', '=', true]]);
            const contracts = await this._count('hop_dong_lao_dong', []);
            const leaves = await this._count('nghi_phep', [['trang_thai', 'in', ['cho_duyet', 'nhap']]]);
            const candidates = await this._count('ung_vien_tuyen_dung', [['trang_thai', 'in', ['moi', 'sang_loc', 'phong_van']]]);
            const departments = await this._read('phong_ban', [], ['ten_phong_ban'], 8, 'ten_phong_ban asc');
            const recentEmployees = await this._read('nhan_vien', [['active', '=', true]], ['ho_ten', 'ma_dinh_danh', 'email_cong_ty', 'que_quan', 'image_1920', 'phong_ban_id', 'chuc_vu_id', 'trang_thai'], 6, 'id desc');
            recentEmployees.forEach(function (employee) {
                employee.image_url = employee.image_1920 ? '/web/image/nhan_vien/' + employee.id + '/image_1920' : false;
            });
            const recentContracts = await this._read('hop_dong_lao_dong', [], ['ma_hop_dong', 'nhan_vien_id', 'ngay_bat_dau', 'ngay_ket_thuc', 'trang_thai'], 5, 'id desc');
            const recentCandidates = await this._read('ung_vien_tuyen_dung', [], ['ho_ten', 'email', 'so_dien_thoai', 'trang_thai'], 5, 'id desc');
            const statusCounts = await Promise.all([
                this._count('nhan_vien', [['trang_thai', '=', 'dang_lam'], ['active', '=', true]]),
                this._count('nhan_vien', [['trang_thai', '=', 'thu_viec'], ['active', '=', true]]),
                this._count('nhan_vien', [['trang_thai', '=', 'tam_nghi'], ['active', '=', true]]),
                this._count('nhan_vien', [['trang_thai', '=', 'da_nghi']]),
            ]);

            this.data = {
                stats: [
                    { label: 'Nhân viên', value: total, icon: 'fa-users', tone: 'blue', action: 'nhan_su.action_nhan_vien' },
                    { label: 'Đang làm', value: working, icon: 'fa-check-circle', tone: 'green', action: 'nhan_su.action_nhan_vien' },
                    { label: 'Thử việc', value: probation, icon: 'fa-clock-o', tone: 'purple', action: 'nhan_su.action_nhan_vien' },
                    { label: 'Hợp đồng', value: contracts, icon: 'fa-file-text-o', tone: 'cyan', action: 'nhan_su.action_hop_dong_lao_dong' },
                    { label: 'Nghỉ chờ duyệt', value: leaves, icon: 'fa-calendar', tone: 'orange', action: 'nhan_su.action_nghi_phep' },
                    { label: 'Ứng viên', value: candidates, icon: 'fa-id-card-o', tone: 'pink', action: 'nhan_su.action_ung_vien_tuyen_dung' },
                ],
                departments: departments,
                recentEmployees: recentEmployees,
                contracts: recentContracts,
                candidates: recentCandidates,
                statusBars: [
                    { label: 'Đang làm', value: statusCounts[0], percent: total ? Math.round(statusCounts[0] * 100 / total) : 0, tone: 'green' },
                    { label: 'Thử việc', value: statusCounts[1], percent: total ? Math.round(statusCounts[1] * 100 / total) : 0, tone: 'purple' },
                    { label: 'Tạm nghỉ', value: statusCounts[2], percent: total ? Math.round(statusCounts[2] * 100 / total) : 0, tone: 'orange' },
                    { label: 'Đã nghỉ', value: statusCounts[3], percent: (total + statusCounts[3]) ? Math.round(statusCounts[3] * 100 / (total + statusCounts[3])) : 0, tone: 'red' },
                ],
            };
        },

        _onOpenAction: function (ev) {
            const action = ev.currentTarget.dataset.action;
            if (action) {
                this.do_action(action);
            }
        },
    });

    core.action_registry.add('nhan_su_hr_dashboard', HrDashboard);
    return HrDashboard;
});
