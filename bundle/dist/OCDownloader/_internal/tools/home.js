/** 
 * jQuery element references 
 */
let $div_console_box = $('#div_console_box');
let $ul_console_list = $('#ul_console_list');
let $div_queue_box = $('#div_queue_box');
let $ul_queue_list = $('#ul_queue_list');

/** 
 * Initialize document behavior when it is ready
 */
$(document).ready(function () {
    $('#btn_clear_console').on('click', function () {
        $ul_console_list.html(''); // Clear console list
    })

    $('#btn_clear_queue').on('click', function () {
        $ul_queue_list.html(''); // Clear queue list
    })
});

/**
 * Appends a string to the console or updates the last console item if it matches a prefix.
 * @param {string} str The message string to send.
 * @returns {Promise} Resolves after the message is appended or updated.
 */
function send_message(str) {
    return new Promise(function (resolve, reject) {
        try {

            /**
             * Appends a string to the console list and scrolls the console box to the bottom.
             * @param {string} str The message string to append.
             */
            function append_str(str) {
                const li = document.createElement("li");
                li.textContent = str;
                $ul_console_list[0].appendChild(li );
                $div_console_box.scrollTop($div_console_box[0].scrollHeight);
            }

            /**
             * Updates the last console item if it matches the given prefix, otherwise appends a new item.
             * @param {string} str The message string to check or append.
             * @param {string} prefix The prefix to check for.
             */
            function updateLastListItem(str, prefix) {
                const $li_last_li = $ul_console_list.children().last();
                if ($li_last_li.length === 0) {
                    append_str(str); // If no children, append the new message
                } else {
                    const str_last_message = $li_last_li.text();
                    if (str.startsWith(prefix) || str_last_message.startsWith(prefix)) {
                        $li_last_li.text(str); // If prefix matches, update the last item
                    } else {
                        append_str(str); // Otherwise, append a new item
                    }
                }
            }

            if (str.startsWith('[youtube]')) {
                updateLastListItem(str, '[youtube]');
                resolve();
            } else if (str.startsWith('[download]')) {
                updateLastListItem(str, '[download]');
                resolve();
            } else if (str.startsWith('[enable_spinner]')) {
                $('#div_busy').show(); // Show spinner
                resolve();
            } else if (str.startsWith('[disable_spinner]')) {
                $('#div_busy').hide(); // Show spinner
                resolve();
            } else if (str.startsWith('[VideoConvertor]')) {
                append_str(str);
                append_str('Video conversion may take a while');
                resolve();
            } else {
                append_str(str);
                resolve();
            }
        } catch (er) {
            reject(er);
        }
    });
}

/**
 * Appends a message to the queue and scrolls the queue box to the bottom.
 * @param {string} str The message string to add to the queue.
 * @returns {Promise} Resolves after the message is added to the queue.
 */
function send_queue(str) {
    return new Promise(function (resolve, reject) {
        try {
            $ul_queue_list.append(`<li class="user-select">${str}</li>`);
            $div_queue_box.scrollTop($div_queue_box[0].scrollHeight);
            resolve();
        } catch (er) {
            reject(er);
        }
    })
}
