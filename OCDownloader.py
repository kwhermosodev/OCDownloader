import json
import sys
import os
import csv
import requests
import re
import threading
import concurrent.futures
from tkinter import filedialog
import webview
from ffmpeg_progress_yield import FfmpegProgress
from subprocess import CREATE_NO_WINDOW
import yt_dlp as ytdl
import time
import asyncio

obj_window = None
bool_is_abort_requested = False
str_program_path = None
str_tools_path = None
str_csv_path = None
str_config_name = 'config.json'
str_csv_name = 'OCDList.csv'
arr_csv_field_names = ['sub_folder','artist','title','media_type_audio_or_video','max_width_in_pixels', 'url']  # csv header list
class_cancel_flag = threading.Event()

# True if a new file was uploaded valid
# Remains false if the uploaded file was retrieved from memory or fails validation.
bool_is_csv_validated = False 

def fn_send_message(str):
    try:
        if obj_window:
            str_json = json.dumps(str)
            obj_window.evaluate_js(f'fn_send_message({str_json})')            
    except Exception as ex:
        raise ex
    
def fn_send_queue(str, int_q_index):
    try:
        str_json = json.dumps(str)
        obj_window.evaluate_js(f'fn_send_queue({str_json}, {int_q_index})')            
    except Exception as ex:
        raise ex
    
class class_stream_redirector:
    def write(self, message):
        if(message.strip()):
            fn_send_message(message)
    def flush(self):
        pass
sys.stdout = class_stream_redirector()
sys.stderr = class_stream_redirector()

def fn_get_paths():
    global str_program_path, str_tools_path
    try:
        if getattr(sys, 'frozen', False):
            str_program_path = os.path.abspath(os.path.dirname(sys.executable))
            str_tools_path = os.path.join(str_program_path,'_internal','tools') 
        else:
            str_program_path = os.path.abspath(os.path.dirname(__file__))
            str_tools_path = os.path.join(str_program_path,'tools')       
    except Exception as ex:
        fn_send_message(str(ex))

def fn_save_settings():
    try:
        dict_settings = {'str_csv_path': f'{str_csv_path}'} 
        str_settings_path = os.path.join(str_program_path, str_config_name) 
        with open(str_settings_path, 'w') as outfile:
            json.dump(dict_settings, outfile)
    except Exception as ex:
        fn_send_message(str(ex))

def fn_load_settings():
    try:
        global str_csv_path
        str_config_path = os.path.join(str_program_path, str_config_name)
        if(os.path.exists(str_config_path)):
            with open(str_config_path, 'r') as openfile:
                json_object = json.load(openfile)
                str_csv_path = json_object['str_csv_path']
        else:
            fn_save_settings()
    except Exception as ex:
        fn_send_message(str(ex))

def fn_create_csv(e):
    try:
        str_default_csv_path = os.path.join(str_program_path, str_csv_name) 
        if(os.path.exists(str_default_csv_path)):
            fn_send_message(f'{str_csv_name} already exists in the parent directory. Operation aborted.') 
            with open(str_default_csv_path, 'w', newline = '') as csvfile: 
                writer = csv.DictWriter(csvfile, fieldnames = arr_csv_field_names)
                writer.writeheader()
            fn_send_message(f'{str_csv_name} created succesfully.') 
    except Exception as ex:
        fn_send_message(str(ex))

def fn_upload_csv(e):
    global bool_is_csv_validated
    global str_csv_path 
    uploaded_file = filedialog.askopenfilename( 
        initialdir = "/", 
        title = "OCDownloader: Select a CSV File", 
        filetypes = [("CSV files", "*.csv")] 
    )
    if(fn_mt_validate_csv(uploaded_file)): 
        str_csv_path = uploaded_file
        fn_save_settings()
        bool_is_csv_validated = True

def fn_is_url_reachable(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception as ex:
        return False

def fn_validate_row(row, int_row_index):
    try:        
        bool_is_row_valid = True
        str_sub_folder = row[0]
        str_title = row [2]
        str_media_type = row[3]
        str_max_width = row[4]
        str_url = row[5]
        str_message = f'Row {int_row_index}/] '
        
        if str_sub_folder and not re.match(r'^[\w\-.\\/]+$', str_sub_folder):
            str_message += f"Invalid sub_folder format: {str_sub_folder}. "
            bool_is_row_valid = False  
        if not str_title:
            str_message += f"Title field is empty. "
            bool_is_row_valid = False
        if str_media_type not in ['audio', 'video']:
            str_message += f"Invalid media_type: {str_media_type}. " 
            bool_is_row_valid = False
        if str_media_type == 'video':
            try:
                str_max_width = int(str_max_width)
                if str_max_width <= 0:
                    str_message += f"Invalid max_width: {str_max_width}. "
                    bool_is_row_valid = False
            except ValueError:
                str_message += f"Invalid max_width: {str_max_width}. "
                bool_is_row_valid = False
        if not str_url:
            str_message += f"URL is empty. "
            bool_is_row_valid = False
        else:
            if not fn_is_url_reachable(str_url):
                str_message += f"URL is not reachable. "
                bool_is_row_valid = False
        if not bool_is_row_valid:
            fn_send_message(str_message)
        return bool_is_row_valid
    except Exception as ex:
        fn_send_message(str(ex))

def fn_mt_validate_csv(path):
    global bool_is_csv_validated
    try:
        fn_send_message("Performing CSV validation. Each URL is being tested as well. Please wait.")
        if path:
            if os.path.exists(path):
                with open(path, 'r', newline='', encoding='utf-8') as upfile:
                    reader = csv.reader(upfile)
                    headers = next(reader)

                    if headers != arr_csv_field_names:
                        fn_send_message(f"Invalid headers. The file should only contain these headers: {arr_csv_field_names}")
                        return False
                    
                    rows_to_validate = list(reader)
                    int_rows_for_validation = len(rows_to_validate)
                    int_validated_rows = 0
                    fn_send_message(f'{int_rows_for_validation} rows are being validated')
                    bool_total_check = True
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        results = [
                            executor.submit(fn_validate_row, row, row_index) for row_index, row in enumerate(rows_to_validate, start=1)
                            ]
                        for future in concurrent.futures.as_completed(results):
                            bool_is_row_valid = future.result()
                            int_validated_rows += 1
                            fn_send_message(f'[Validating] {int_validated_rows}/{int_rows_for_validation}')
                            if not bool_is_row_valid:
                                bool_total_check = False
                    
                    if bool_total_check:
                        fn_send_message('CSV contents are valid.')
                        bool_is_csv_validated = True
                    else:
                        fn_send_message('CSV contents are invalid.')
                        bool_is_csv_validated = False
                    return bool_total_check
    except Exception as ex:
        fn_send_message(str(ex))

def fn_check_working_csv():
    try:
        if(str_csv_path and os.path.exists(str_csv_path)):
            arr_csv_working_path = str_csv_path.split('\\')
            fn_send_message(f'{arr_csv_working_path[-1]} was found from a previous session and auto-loaded.')
    except Exception as ex:
        fn_send_message(str(ex))

def orig_fn_download_file(row, int_row_index, int_row_count):
    int_message_index = int(time.time() * 1000)
    str_queue_pos = f'{int_row_index}/{int_row_count}'

    try:
               
        str_downloads_path = os.path.join(str_program_path, 'Downloads')
        str_ffmpeg_path = os.path.join(str_tools_path, 'ffmpeg.exe')
        sub_folder = row[0]
        if sub_folder:
            sub_folder_parts = re.split(r'[\\\/]', sub_folder)
            sub_folder = os.sep.join(sub_folder_parts)
        artist = row [1]
        title = row [2]
        media_type = row[3]
        max_width_in_pixels = int(row[4]) if media_type == 'video' else 0
        url = row[5]
        
        sub_folder_path = os.path.join(str_downloads_path, sub_folder)
        os.makedirs(sub_folder_path, exist_ok=True)
        
        final_filename = f"{artist} - {title}" 
        ydl_opts_check = {
            'ffmpeg_location': str_ffmpeg_path,
            'quiet': True,
        }
        
        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title}', int_message_index)
        
        with ytdl.YoutubeDL(ydl_opts_check) as ydl:
        
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            best_format = None
            lowest_width_threshold = 80 * max_width_in_pixels
            str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp3")
            
            if media_type == 'video':
                str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp4")
            
            if os.path.exists(str_final_path_to_check):
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Aborted]', int_message_index)
                return

            if media_type == 'video':
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Looking for stream]', int_message_index)
                best_format = None
                for format in formats:
                    if format.get('ext') == 'mp4' and format.get('vcodec') != 'none' and format.get('acodec') != 'none':
                        if lowest_width_threshold < format.get('width', 0) <= max_width_in_pixels:
                            if best_format is None or format.get('width') > best_format.get('width'):
                                best_format = format

            if best_format:

                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Found format: {best_format["ext"]}]', int_message_index)
                ydl_opts = { 
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'format': best_format['format_id'],
                    'quiet': True,
                }
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading]', int_message_index) 
                fn_send_message('[enable_spinner]')
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            else:
                ydl_opts = {
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'overwrites': True,
                }
                if media_type == 'audio':
                    ydl_opts.update({'format': 'bestaudio/best'})
                elif media_type == 'video':
                    format_string = f'bestvideo[width<={max_width_in_pixels}]+bestaudio/best'
                    ydl_opts.update({'format': format_string})
                else:
                    raise ValueError("Invalid media type. Choose 'audio' or 'video'.")
                if media_type == 'video':
                    fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading A/V Stream to Merge]', int_message_index)
                else:
                    fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading Audio Stream]', int_message_index)
                fn_send_message('[enable_spinner]')
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.download([url])
                    if result == 0 and media_type == 'audio':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloaded File Extension is {str_file_extension}]', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Converting to MP3]', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file, '-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp3")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)
                    elif result == 0 and media_type == 'video':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloaded File Extension is {str_file_extension}]', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Converting to MP4]', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file,'-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp4")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)

        return True
    except Exception as ex:
        fn_send_message(str(ex))

def fn_download_file(row, int_row_index, int_row_count, int_message_index):
    global bool_is_abort_requested
    if bool_is_abort_requested:
        fn_send_queue(f'{str_queue_pos} {sub_folder}: {row [1]} - {row [2]} [Aborted. Manually aborted.]', int_message_index)
        return
    str_queue_pos = f'{int_row_index}/{int_row_count}'
    
    try:
               
        str_downloads_path = os.path.join(str_program_path, 'Downloads')
        str_ffmpeg_path = os.path.join(str_tools_path, 'ffmpeg.exe')
        sub_folder = row[0]
        if sub_folder:
            sub_folder_parts = re.split(r'[\\\/]', sub_folder)
            sub_folder = os.sep.join(sub_folder_parts)
        artist = row [1]
        title = row [2]
        media_type = row[3]
        max_width_in_pixels = int(row[4]) if media_type == 'video' else 0
        url = row[5]
        
        sub_folder_path = os.path.join(str_downloads_path, sub_folder)
        os.makedirs(sub_folder_path, exist_ok=True)
        
        final_filename = f"{artist} - {title}" 
        ydl_opts_check = {
            'ffmpeg_location': str_ffmpeg_path,
            'quiet': True,
        }
        
        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title}', int_message_index)
        
        with ytdl.YoutubeDL(ydl_opts_check) as ydl:
        
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            best_format = None
            lowest_width_threshold = 80 * max_width_in_pixels
            str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp3")
            
            if media_type == 'video':
                str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp4")
            
            if os.path.exists(str_final_path_to_check):
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Aborted. File exists]', int_message_index)
                return

            if media_type == 'video':
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Looking for stream]', int_message_index)
                best_format = None
                for format in formats:
                    if format.get('ext') == 'mp4' and format.get('vcodec') != 'none' and format.get('acodec') != 'none':
                        if lowest_width_threshold < format.get('width', 0) <= max_width_in_pixels:
                            if best_format is None or format.get('width') > best_format.get('width'):
                                best_format = format

            if best_format:

                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Found format: {best_format["ext"]}]', int_message_index)
                ydl_opts = { 
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'format': best_format['format_id'],
                    'quiet': True,
                }
                fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading]', int_message_index) 
                fn_send_message('[enable_spinner]')
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            else:
                ydl_opts = {
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'overwrites': True,
                }
                if media_type == 'audio':
                    ydl_opts.update({'format': 'bestaudio/best'})
                elif media_type == 'video':
                    format_string = f'bestvideo[width<={max_width_in_pixels}]+bestaudio/best'
                    ydl_opts.update({'format': format_string})
                else:
                    raise ValueError("Invalid media type. Choose 'audio' or 'video'.")
                if media_type == 'video':
                    fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading A/V Stream to Merge]', int_message_index)
                else:
                    fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloading Audio Stream]', int_message_index)
                fn_send_message('[enable_spinner]')
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.download([url])
                    if result == 0 and media_type == 'audio':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloaded File Extension is {str_file_extension}]', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Converting to MP3]', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file, '-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp3")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)
                    elif result == 0 and media_type == 'video':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Downloaded File Extension is {str_file_extension}]', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_queue(f'{str_queue_pos} {sub_folder}: {artist} - {title} [Converting to MP4]', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file,'-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp4")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)

        return True
    except Exception as ex:
        fn_send_message(str(ex))

def orig_fn_mt_download_from_csv(e):
    global bool_is_abort_requested
    try:
        if not fn_mt_validate_csv(str_csv_path):
            fn_send_message('Download Cancelled Due To Validation Issues.')
            return
        with open(str_csv_path, mode='r', newline='') as file:
                    
            reader = csv.reader(file)
            headers = next(reader)
            rows_to_validate = list(reader)
            int_rows_for_validation = len(rows_to_validate)
            fn_send_message(f'Downloading {int_rows_for_validation} items.')           
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = [
                        executor.submit(fn_download_file, row, row_index, int_rows_for_validation) for row_index, row in enumerate(rows_to_validate, start=1)
                    ]
                for future in concurrent.futures.as_completed(results):
                    result = future.result()
        fn_send_message('[disable_spinner]')
        fn_send_message("Download and conversion complete.")
        fn_send_queue("Download and conversion complete.")
    except Exception as ex:
        fn_send_message(str(ex))

def fn_mt_download_from_csv(e):
    global bool_is_abort_requested
    try:
        if not fn_mt_validate_csv(str_csv_path):
            fn_send_message('Download Cancelled Due To Validation Issues.')
            return
        with open(str_csv_path, mode='r', newline='') as file:
                    
            reader = csv.reader(file)
            headers = next(reader)
            rows_to_validate = list(reader)
            int_rows_for_validation = len(rows_to_validate)
            fn_send_message(f'Downloading {int_rows_for_validation} items.')           
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = []
                for row_index, row in enumerate(rows_to_validate, start=1):
                    
                    if bool_is_abort_requested:
                        break
                    
                    int_message_index = int(time.time() * 1000)
                    fn_send_queue(f'{row_index} {int_rows_for_validation}: {row[1]} - {row[2]}', int_message_index)
                    future = executor.submit(fn_download_file, row, row_index, int_rows_for_validation, int_message_index)
                    results.append(future)

                for future in concurrent.futures.as_completed(results):
                    result = future.result()
        
        if bool_is_abort_requested:
            fn_send_message("Download Aborted by User.")
            bool_is_abort_requested = False
            return 
        fn_send_message('[disable_spinner]')
        fn_send_message("Download and conversion complete.")
        fn_send_queue("Download and conversion complete.", int(time.time() * 1000))
    except Exception as ex:
        fn_send_message(str(ex))

def abort(e):  # Function to abort the operation
    global bool_is_abort_requested
    bool_is_abort_requested = True


def bind(obj_window):
    try:
        fn_load_settings()
        fn_send_message(f'Initializing...')
        fn_check_working_csv()
        fn_send_message(f'Initialized.')
        btn_create_csv = obj_window.dom.get_element('#btn_create_csv')
        btn_create_csv.on('click', lambda e: fn_create_csv(e))       
        btn_upload_csv = obj_window.dom.get_element('#btn_upload_csv')
        btn_upload_csv.on('click', lambda e: fn_upload_csv(e))
        btn_download_from_csv = obj_window.dom.get_element('#btn_download_from_csv')
        btn_download_from_csv.on('click', lambda e: fn_mt_download_from_csv(e))
        btn_abort = obj_window.dom.get_element('#btn_abort')
        btn_abort.on('click', lambda e: abort(e))
    except Exception as ex:
        fn_send_message(str(ex))

if __name__ == '__main__':
    fn_get_paths()
    str_html_path = os.path.join(str_tools_path,'home.html')
    obj_window = webview.create_window('OCDownloader', str_html_path, width=800, height=800, )
    webview.start(bind, obj_window)