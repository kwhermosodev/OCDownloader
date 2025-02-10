$(document).ready(function () {
    fn_console_resize();
    $(window).on('resize', function () {
        fn_console_resize();
    })
})

function fn_console_resize() {

    const arr_ctrl_fixed_heights = [
        $("#h1_title").innerHeight(),
        $("#ul_tab_list").innerHeight(),
        $('#div_ctrl').innerHeight(),
    ]

    const arr_abt_fixed_heights = [
        $("#h1_title").innerHeight(),
        $("#ul_tab_list").innerHeight()
    ]

    const flt_ctrl_fixed_heights = arr_ctrl_fixed_heights.reduce((a, b) => a + b, 0)
    const flt_abt_fixed_heights = arr_abt_fixed_heights.reduce((a, b) => a + b, 0)
    const win_in_height = window.innerHeight;
    $('#div_csl').innerHeight(win_in_height - flt_ctrl_fixed_heights - 100);
    $('#div_abt').innerHeight(win_in_height - flt_abt_fixed_heights - 100);
}

function fn_send_message(str_message, str_li_id){
    if(str_li_id && str_li_id.length > 0){
        $li = $(`#${str_li_id}`);
        if($li.length > 0){
            $li.text(str_message);
        }else{
            fn_append_message(str_message, str_li_id);
        }
    }else{
        fn_append_message(str_message, '');
    }    
}

function fn_append_message(str_message, str_li_id){
    if(str_li_id.length > 0){
        $("#ul_csl").append(`<li id=${str_li_id}>${str_message}</li>`)
    }else{
        $("#ul_csl").append(`<li>${str_message}</li>`)
    }    
}

arr_libraries = []