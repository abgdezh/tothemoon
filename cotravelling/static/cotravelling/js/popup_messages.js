let button_ok = '<button id="popup_ok_btn" class="btn_boderless_action btn_small btn_popup" onclick="hide_popup();" style="margin-left: auto;">ОК</button>'
let button_cancel = '<button id="popup_deny_btn" class="btn_boderless_action btn_small btn_popup" onclick="hide_popup();" style="margin-left: auto;">Отменить</button>'
let button_sign_in = '<button id="popup_sign_in_btn" class="btn_boderless_action btn_small btn_popup" style="margin-left: auto;">Войти</button>'

// всплывающее окно при добавлении новой поездки
function show_added_new_trip_popup(notification_allowed) {
    var message = "Мы уже начали искать для вас попутчиков! Как только новый участник присоединится к поездке, мы отправим сообщение вконтакте."
    if (!notification_allowed) {
        message += " Нажмите кнопку \"Получать уведомления\", чтобы не пропустить сообщения."
    }

    var data = {
        popup_title: "Ваша поездка добавлена!",
        popup_message: message
    }

    var template = $("#popup-template").html()

    var html = Mustache.render(template, data)
    $("body").append(html)
    $("#popup-control-buttons").append(button_ok)
}

// всплывающеие окно входы с редирект урлом в кавычках
function show_need_auth_popup(redirect_url) {
    var message = "Войдите, чтобы получать уведомления о новых поездках!"

    var data = {
        popup_title: "Уведомления о новых поездках",
        popup_message: message
    }

    var template = $("#popup-template").html()

    var html = Mustache.render(template, data)
    $("body").append(html)
    $("#popup-control-buttons").append(button_sign_in)
    $("#popup_sign_in_btn").click(function () { location.href='/login/vk-oauth2/?next=' + encodeURIComponent(redirect_url.slice(1, -1)) + ';'} )
}

function hide_popup() {
    document.getElementById("popup-window").style.display = 'none';
}

let search_params = new URLSearchParams(window.location.search)

var notification_allowed = false

if (search_params.has("notify_allowed")) {
    notification_allowed = (search_params.get("notify_allowed") == '1')
}

if (search_params.has("added_trip")) {
    if (search_params.get("added_trip") == 'true') {
        show_added_new_trip_popup(notification_allowed)
    }
}

if (search_params.has("need_auth")) {
    if (search_params.get("need_auth") == 'true') {
        show_need_auth_popup(search_params.get("redirect_url"))
    }
}
