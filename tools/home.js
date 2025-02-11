$(document).ready(function () {
    fn_load_libraries();
    fn_console_resize();    
    $(window).on('resize', function () {
        fn_console_resize();
    })

    $("#btn_clr").on("click", function(){
        $("#ul_csl").html('');
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

function fn_send_message(str_message, str_li_id) {
    if (str_li_id && str_li_id.length > 0) {
        $li = $(`#${str_li_id}`);
        if ($li.length > 0) {
            $li.text(str_message);
        } else {
            fn_append_message(str_message, str_li_id);
        }
    } else {
        fn_append_message(str_message, '');
    }
}

function fn_append_message(str_message, str_li_id) {
    if (str_li_id.length > 0) {
        $("#ul_csl").append(`<li class="user-select" id=${str_li_id}>${str_message}</li>`)
    } else {
        $("#ul_csl").append(`<li class="user-select">${str_message}</li>`)
    }
}

arr_libraries = ["python - 3.13.1", "altgraph - 0.17.4", "bottle - 0.13.2", "certifi - 2025.1.31", "cffi - 1.17.1", "charset-normalizer - 3.4.1", "clr_loader - 0.2.7.post0", "et_xmlfile - 2.0.0", "ffmpeg-progress-yield - 0.11.3", "idna - 3.10", "numpy - 2.2.2", "openpyxl - 3.1.5", "packaging - 24.2", "pandas - 2.2.3", "pefile - 2023.2.7", "pip - 24.3.1", "proxy_tools - 0.1.0", "psutil - 6.1.1", "pycparser - 2.22", "pyinstaller - 6.12.0", "pyinstaller-hooks-contrib - 2025.1", "python-dateutil - 2.9.0.post0", "pythonnet - 3.0.5", "pytz - 2025.1", "pywebview - 5.4", "pywin32-ctypes - 0.2.3", "requests - 2.32.3", "setuptools - 75.8.0", "six - 1.17.0", "typing_extensions - 4.12.2", "tzdata - 2025.1", "urllib3 - 2.3.0", "yt-dlp - 2025.1.26"];

function fn_load_libraries(){  
    for(let i=0; i<arr_libraries.length; i++){
        let str_lib = arr_libraries[i];
        $("#ul_libraries").append(`<li class="user-select">${str_lib}</li>`);
    }
}