$(document).ready(function () {

})

function fn_append_list_item(str, str_ul_id) {
    return new Promise(function (resolve, reject) {
        try {
            $("#" + str_ul_id).append('<li ${name}class="user-select">' + str + '</li>');
            resolve();
        } catch (error) {
            reject(error);
        }
    })
}

function fn_update_last_list_item(str, str_prefix, str_ul_id) {
    return new Promise(function (resolve, reject) {
        try {
            let $li_last_li = $("#" + str_ul_id + " li:last");
            if ($li_last_li.length > 0) {
                let str_last_str = $li_last_li.text();
                if (str_last_str.startsWith(str_prefix) && str.startsWith(str_prefix)) {
                    $li_last_li.text(str)
                } else {
                    fn_append_list_item(str, str_ul_id)
                }
            } else {
                fn_append_list_item(str, str_ul_id)
            }
            resolve();
        } catch (error) {
            reject(error);
        }
    })
}

function fn_send_message(str, str_message_id = null) {
    return new Promise(function (resolve, reject) {
        try {
            if (str_message_id) {
                $li_message_li = $("#" + str_message_id);
                if ($li_message_li.length > 0) {
                    $li_message_li.text(str);
                } else {
                    $("#ul_console_list").append(`<li id="${str_message_id}" class="no-wrap user-select">` + str + '</li>');
                }
            } else if (str.startsWith('[Validating]')) {
                fn_update_last_list_item(str, '[Validating]', "ul_console_list")
            } else if (str.startsWith('[enable_spinner]')) {
                $('#div_busy').show();
            } else if (str.startsWith('[disable_spinner]')) {
                $('#div_busy').hide();
            } else {
                fn_append_list_item(str, 'ul_console_list');
            }
            resolve();
        } catch (error) {
            reject(error);
        }
    })
}