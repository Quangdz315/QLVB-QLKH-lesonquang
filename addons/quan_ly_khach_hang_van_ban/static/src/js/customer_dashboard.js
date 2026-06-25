odoo.define('quan_ly_khach_hang_van_ban.customer_dashboard', function (require) {
    'use strict';

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const QWeb = core.qweb;

    const CustomerDashboard = AbstractAction.extend({
        template: 'quan_ly_khach_hang_van_ban.CustomerDashboard',

        events: {
            'click .o_ql_dashboard_card': '_onOpenAction',
            'click .o_ql_dash_link': '_onOpenAction',
        },

        init: function () {
            this._super.apply(this, arguments);
            this.data = {};
        },

        willStart: function () {
            return Promise.all([this._super.apply(this, arguments), this._loadData()]);
        },

        start: function () {
            this.$el.html(QWeb.render('quan_ly_khach_hang_van_ban.CustomerDashboardContent', { data: this.data }));
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
            const totalCustomers = await this._count('res.partner', [['is_khach_hang', '=', true]]);
            const priorityCustomers = await this._count('res.partner', [['is_khach_hang', '=', true], ['muc_do_uu_tien', '=', 'cao']]);
            const signedCustomers = await this._count('res.partner', [['is_khach_hang', '=', true], ['trang_thai_cham_soc', '=', 'da_ky_hop_dong']]);
            const incomingDocs = await this._count('van_ban_den', [['khach_hang_id', '!=', false]]);
            const outgoingDocs = await this._count('van_ban_di', [['khach_hang_id', '!=', false]]);
            const expiredDocs = await this._count('van_ban_den', [['khach_hang_id', '!=', false], ['trang_thai_ho_so', '=', 'het_han']]);
            const customers = await this._read('res.partner', [['is_khach_hang', '=', true]], ['ma_khach_hang', 'name', 'phone', 'email', 'nhan_vien_phu_trach_id', 'trang_thai_cham_soc', 'muc_do_uu_tien', 'tong_so_van_ban'], 6, 'id desc');
            const incoming = await this._read('van_ban_den', [['khach_hang_id', '!=', false]], ['so_van_ban_den', 'ten_van_ban', 'khach_hang_id', 'nhom_ho_so', 'trang_thai_ho_so', 'ngay_het_han'], 5, 'id desc');
            const outgoing = await this._read('van_ban_di', [['khach_hang_id', '!=', false]], ['so_van_ban_di', 'ten_van_ban', 'khach_hang_id', 'nhom_ho_so', 'trang_thai_ho_so', 'ngay_het_han'], 5, 'id desc');
            const stateCounts = await Promise.all([
                this._count('res.partner', [['is_khach_hang', '=', true], ['trang_thai_cham_soc', '=', 'moi']]),
                this._count('res.partner', [['is_khach_hang', '=', true], ['trang_thai_cham_soc', '=', 'dang_cham_soc']]),
                this._count('res.partner', [['is_khach_hang', '=', true], ['trang_thai_cham_soc', '=', 'da_ky_hop_dong']]),
                this._count('res.partner', [['is_khach_hang', '=', true], ['trang_thai_cham_soc', '=', 'tam_dung']]),
            ]);

            this.data = {
                stats: [
                    { label: 'Tổng KH', value: totalCustomers, icon: 'fa-address-book-o', tone: 'blue', action: 'quan_ly_khach_hang_van_ban.action_khach_hang_ho_so' },
                    { label: 'Ưu tiên cao', value: priorityCustomers, icon: 'fa-star', tone: 'orange', action: 'quan_ly_khach_hang_van_ban.action_khach_hang_ho_so' },
                    { label: 'Đã ký HĐ', value: signedCustomers, icon: 'fa-handshake-o', tone: 'green', action: 'quan_ly_khach_hang_van_ban.action_khach_hang_ho_so' },
                    { label: 'VB đến KH', value: incomingDocs, icon: 'fa-inbox', tone: 'purple', action: 'quan_ly_khach_hang_van_ban.action_van_ban_den_khach_hang' },
                    { label: 'VB đi KH', value: outgoingDocs, icon: 'fa-paper-plane', tone: 'cyan', action: 'quan_ly_khach_hang_van_ban.action_van_ban_di_khach_hang' },
                    { label: 'Hết hạn', value: expiredDocs, icon: 'fa-exclamation-triangle', tone: 'red', action: 'quan_ly_khach_hang_van_ban.action_van_ban_den_khach_hang' },
                ],
                customers: customers,
                incoming: incoming,
                outgoing: outgoing,
                stateBars: [
                    { label: 'Mới', value: stateCounts[0], percent: totalCustomers ? Math.round(stateCounts[0] * 100 / totalCustomers) : 0, tone: 'blue' },
                    { label: 'Đang chăm sóc', value: stateCounts[1], percent: totalCustomers ? Math.round(stateCounts[1] * 100 / totalCustomers) : 0, tone: 'purple' },
                    { label: 'Đã ký hợp đồng', value: stateCounts[2], percent: totalCustomers ? Math.round(stateCounts[2] * 100 / totalCustomers) : 0, tone: 'green' },
                    { label: 'Tạm dừng', value: stateCounts[3], percent: totalCustomers ? Math.round(stateCounts[3] * 100 / totalCustomers) : 0, tone: 'red' },
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

    core.action_registry.add('qlkh_customer_dashboard', CustomerDashboard);
    return CustomerDashboard;
});
