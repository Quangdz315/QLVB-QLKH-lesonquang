odoo.define('quan_ly_van_ban.document_dashboard', function (require) {
    'use strict';

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const QWeb = core.qweb;

    const DocumentDashboard = AbstractAction.extend({
        template: 'quan_ly_van_ban.DocumentDashboard',

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
            this.$el.html(QWeb.render('quan_ly_van_ban.DocumentDashboardContent', { data: this.data }));
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
            const incoming = await this._count('van_ban_den', []);
            const outgoing = await this._count('van_ban_di', []);
            const urgentIncoming = await this._count('van_ban_den', [['ai_can_xu_ly_gap', '=', true]]);
            const urgentOutgoing = await this._count('van_ban_di', [['ai_can_xu_ly_gap', '=', true]]);
            const internalDocs = await this._count('van_ban_di', [['nhom_van_ban', 'in', ['noi_bo', 'nhan_vien', 'phong_ban', 'chung']]]);
            const partnerDocs = await this._count('van_ban_den', [['nhom_van_ban', '=', 'co_quan_doi_tac']]);
            const types = await this._count('loai_van_ban', []);
            const recentIncoming = await this._read('van_ban_den', [], ['so_van_ban_den', 'ten_van_ban', 'ngay_den', 'nhom_van_ban', 'nguon_gui_tong_hop', 'ai_ket_qua_nhanh'], 6, 'id desc');
            const recentOutgoing = await this._read('van_ban_di', [], ['so_van_ban_di', 'ten_van_ban', 'nhom_van_ban', 'nguoi_nhan_tong_hop', 'ai_ket_qua_nhanh'], 6, 'id desc');
            const groupCounts = await Promise.all([
                this._count('van_ban_di', [['nhom_van_ban', '=', 'nhan_vien']]),
                this._count('van_ban_di', [['nhom_van_ban', '=', 'phong_ban']]),
                this._count('van_ban_di', [['nhom_van_ban', '=', 'noi_bo']]),
                this._count('van_ban_den', [['nhom_van_ban', '=', 'co_quan_doi_tac']]),
                this._count('van_ban_di', [['nhom_van_ban', '=', 'chung']]),
            ]);
            const totalGroup = groupCounts.reduce((sum, value) => sum + value, 0);

            this.data = {
                stats: [
                    { label: 'VB đến', value: incoming, icon: 'fa-inbox', tone: 'blue', action: 'quan_ly_van_ban.action_van_ban_den' },
                    { label: 'VB đi', value: outgoing, icon: 'fa-paper-plane', tone: 'green', action: 'quan_ly_van_ban.action_van_ban_di' },
                    { label: 'AI cảnh báo', value: urgentIncoming + urgentOutgoing, icon: 'fa-exclamation-triangle', tone: 'red', action: 'quan_ly_van_ban.action_van_ban_den' },
                    { label: 'Nội bộ', value: internalDocs, icon: 'fa-building-o', tone: 'purple', action: 'quan_ly_van_ban.action_van_ban_di' },
                    { label: 'Đối tác gửi', value: partnerDocs, icon: 'fa-external-link', tone: 'orange', action: 'quan_ly_van_ban.action_van_ban_den' },
                    { label: 'Loại VB', value: types, icon: 'fa-tags', tone: 'cyan', action: 'quan_ly_van_ban.action_loai_van_ban' },
                ],
                recentIncoming: recentIncoming,
                recentOutgoing: recentOutgoing,
                groupBars: [
                    { label: 'Gửi nhân viên', value: groupCounts[0], percent: totalGroup ? Math.round(groupCounts[0] * 100 / totalGroup) : 0, tone: 'blue' },
                    { label: 'Gửi phòng ban', value: groupCounts[1], percent: totalGroup ? Math.round(groupCounts[1] * 100 / totalGroup) : 0, tone: 'purple' },
                    { label: 'Nội bộ', value: groupCounts[2], percent: totalGroup ? Math.round(groupCounts[2] * 100 / totalGroup) : 0, tone: 'green' },
                    { label: 'Cơ quan/đối tác', value: groupCounts[3], percent: totalGroup ? Math.round(groupCounts[3] * 100 / totalGroup) : 0, tone: 'orange' },
                    { label: 'Chung', value: groupCounts[4], percent: totalGroup ? Math.round(groupCounts[4] * 100 / totalGroup) : 0, tone: 'cyan' },
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

    core.action_registry.add('qlvb_document_dashboard', DocumentDashboard);
    return DocumentDashboard;
});
