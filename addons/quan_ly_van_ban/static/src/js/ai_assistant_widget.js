odoo.define('quan_ly_van_ban.ai_assistant_widget', function (require) {
    'use strict';

    var core = require('web.core');
    var rpc = require('web.rpc');

    var _t = core._t;

    function mountAiAssistant() {
        if ($('.o_ai_float').length) {
            return;
        }
        var html = '' +
            '<div class="o_ai_float">' +
                '<button type="button" class="o_ai_float_handle" title="Trợ lý AI">' +
                    '<span>Trợ lý AI</span>' +
                    '<strong>?</strong>' +
                '</button>' +
                '<section class="o_ai_float_panel">' +
                    '<header>' +
                        '<div>' +
                            '<strong>Trợ lý AI</strong>' +
                            '<small>Chat với Gemini về QLNS, QLVB, QLKH</small>' +
                        '</div>' +
                        '<button type="button" class="o_ai_close" title="Đóng">&times;</button>' +
                    '</header>' +
                    '<div class="o_ai_chat_tools">' +
                        '<select class="o_ai_scope">' +
                            '<option value="tong_hop">Tổng hợp</option>' +
                            '<option value="nhan_su">Nhân sự</option>' +
                            '<option value="van_ban">Văn bản</option>' +
                            '<option value="khach_hang">Khách hàng</option>' +
                        '</select>' +
                        '<button type="button" class="o_ai_clear" title="Xóa chat"><i class="fa fa-trash-o"></i></button>' +
                    '</div>' +
                    '<div class="o_ai_messages">' +
                        '<div class="o_ai_msg o_ai_msg_bot">' +
                            '<div class="o_ai_bubble">Xin chào, bạn muốn hỏi gì về hệ thống hôm nay?</div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="o_ai_composer">' +
                        '<textarea class="o_ai_question" rows="1" placeholder="Nhập tin nhắn..."></textarea>' +
                        '<button type="button" class="o_ai_send" title="Gửi"><i class="fa fa-paper-plane"></i></button>' +
                    '</div>' +
                '</section>' +
            '</div>';
        $('body').append(html);
    }

    function scrollBottom() {
        var box = $('.o_ai_messages')[0];
        if (box) {
            box.scrollTop = box.scrollHeight;
        }
    }

    function appendMessage(role, text, extraClass) {
        var cls = role === 'user' ? 'o_ai_msg_user' : 'o_ai_msg_bot';
        var body = _.escape(text || '').replace(/\n/g, '<br/>');
        var html = '<div class="o_ai_msg ' + cls + ' ' + (extraClass || '') + '">' +
            '<div class="o_ai_bubble">' + body + '</div>' +
            '</div>';
        $('.o_ai_messages').append(html);
        scrollBottom();
    }

    function openCloseAiAssistant() {
        $('.o_ai_float').toggleClass('o_ai_open');
        scrollBottom();
    }

    function clearAiChat() {
        $('.o_ai_messages').html(
            '<div class="o_ai_msg o_ai_msg_bot"><div class="o_ai_bubble">Mình đã xóa đoạn chat trên màn hình. Bạn hỏi tiếp nhé.</div></div>'
        );
    }

    function askAiAssistant() {
        var $widget = $('.o_ai_float');
        var $input = $widget.find('.o_ai_question');
        var question = ($input.val() || '').trim();
        var scope = $widget.find('.o_ai_scope').val() || 'tong_hop';
        if (!question) {
            return;
        }
        appendMessage('user', question);
        $input.val('').height(38);
        appendMessage('bot', 'Gemini đang suy nghĩ...', 'o_ai_loading');

        rpc.query({
            model: 'qlvb.ai_assistant',
            method: 'ask_from_widget',
            args: [question, scope],
        }).then(function (result) {
            $('.o_ai_loading').last().remove();
            appendMessage('bot', result.answer || 'Gemini chưa trả lời.');
        }).guardedCatch(function (error) {
            $('.o_ai_loading').last().remove();
            var message = error && error.message || _t('Không hỏi được AI.');
            appendMessage('bot', message, 'o_ai_error_msg');
        });
    }

    function autoGrowInput() {
        this.style.height = '38px';
        this.style.height = Math.min(this.scrollHeight, 110) + 'px';
    }

    $(document).ready(function () {
        window.setTimeout(mountAiAssistant, 600);
    });
    $(document).on('click', '.o_ai_float_handle, .o_ai_close', openCloseAiAssistant);
    $(document).on('click', '.o_ai_send', askAiAssistant);
    $(document).on('click', '.o_ai_clear', clearAiChat);
    $(document).on('input', '.o_ai_question', autoGrowInput);
    $(document).on('keydown', '.o_ai_question', function (ev) {
        if (ev.key === 'Enter' && !ev.shiftKey) {
            ev.preventDefault();
            askAiAssistant();
        }
    });
});
