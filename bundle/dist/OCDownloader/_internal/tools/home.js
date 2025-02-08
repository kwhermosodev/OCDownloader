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

function fn_send_message(str) {
    return new Promise(function (resolve, reject) {
        try {
            str_bracket_prefix = str.split(']')[0] + ']';
            arr_prefixes_that_update = [
                '[youtube]',
                '[download]',
                '[Converting]',
                '[Validating]'
            ]
            if(arr_prefixes_that_update.includes(str_bracket_prefix)){
                fn_update_last_list_item(str, str_bracket_prefix, 'ul_console_list');                
            }else{
                if (str.startsWith('[enable_spinner]')) {
                    $('#div_busy').show();
                } else if (str.startsWith('[disable_spinner]')) {
                    $('#div_busy').hide();
                } else if (str.startsWith('[VideoConvertor]')) {
                    fn_append_list_item(str, 'ul_console_list')
                    fn_append_list_item('Video conversion may take a while', 'ul_console_list');
                } else {
                    fn_append_list_item(str, 'ul_console_list');
                }
            }
            $("#div_console_box").scrollTop($("#div_console_box")[0].scrollHeight);
            resolve();            
        } catch (error) {
            reject(error);
        }
    })
}

function fn_send_queue(str, int_queue_id) {
    return new Promise(function (resolve, reject) {
        try {
            $li_queue_member = $("#"+int_queue_id);
            if($li_queue_member.length > 0){
                $li_queue_member.text(str);
            }else{
                $("#ul_queue_list").append(`<li id="${int_queue_id}" class="user-select">` + str + '</li>');
            }
            $("#div_queue_box").scrollTop($("#div_queue_box")[0].scrollHeight);
            resolve();         
        } catch (error) {
            reject(error);
        }
    })
}