import json
import sys
import os
import requests
import re
import threading
import concurrent.futures
from tkinter import filedialog
import yt_dlp as ytdl
from subprocess import CREATE_NO_WINDOW
from ffmpeg_progress_yield import FfmpegProgress
import psutil
import time
import webview
import random
import pandas as pd
import csv

obj_window = None
str_program_path = None
str_tools_path = None
str_config_name = 'config.json'
str_csv_path = None
str_csv_name = 'OCDList.csv'
arr_csv_field_names = ['sub_folder','artist','title','media_type_audio_or_video','max_width_in_pixels', 'url']  # csv header list
bool_is_downloading = False

def fn_send_message(str, str_id=None):
    try:
        if obj_window:
            str_json = json.dumps(str)
            if str_id is None:
                str_id = ''
            str_id_json = json.dumps(str_id)
            obj_window.evaluate_js(f'fn_send_message({str_json},{str_id_json})')
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

class_stop_event = threading.Event() 

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

def fn_get_paths():
    global str_program_path, str_tools_path
    try:
        if getattr(sys, 'frozen', False):
            str_program_path = os.path.abspath(os.path.dirname(sys.executable))
            str_tools_path = os.path.join(sys._MEIPASS, 'tools') if hasattr(sys, '_MEIPASS') else os.path.join(str_program_path, '_internal', 'tools')            
        else:
            str_program_path = os.path.abspath(os.path.dirname(__file__))
            str_tools_path = os.path.join(str_program_path,'tools')       
    except Exception as ex:
        fn_send_message(str(ex))

def fn_create_csv(e):
    try:
        if bool_is_downloading:
            return
        str_default_csv_path = os.path.join(str_program_path, str_csv_name) 
        if(os.path.exists(str_default_csv_path)):
            fn_send_message(f'{str_csv_name} already exists in the parent directory. Operation aborted.') 
            with open(str_default_csv_path, 'w', newline = '') as csvfile: 
                writer = csv.DictWriter(csvfile, fieldnames = arr_csv_field_names)
                writer.writeheader()
            fn_send_message(f'{str_csv_name} created succesfully.') 
    except Exception as ex:
        fn_send_message(str(ex))

def fn_is_url_reachable(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except:
        return False

def fn_read_table(path):
    _, file_extension = os.path.splitext(path)
    if file_extension.lower() == '.csv':
        data = pd.read_csv(path,header=0, skipinitialspace=True)
    elif file_extension.lower() in ['.xls', '.xlsx']:
        data = pd.read_excel(path,header=0,sheet_name=0)
    else:
        raise ValueError("Unsupported file type. Please select a CSV or Excel file.")
    data = data.dropna(how='all')
    return data

def fn_validate_row(row, int_list_index, int_list_length, int_message_index):
    try:        
        boo_total_check = True
        str_sub_folder = row[0]
        str_title = row [2]
        str_media_type = row[3]
        str_max_width = row[4]
        str_url = row[5]
        fn_send_message(f'[Validating] {int_list_index}/{int_list_length}',str(int_message_index))
        str_message = f'[{int_list_index}/{int_list_length}] '        
        if str_sub_folder and not re.match(r'^[\w\-.\\/]+$', str_sub_folder):
            str_message += f"Invalid sub_folder format: {str_sub_folder}. "
            boo_total_check = False  
        if not str_title:
            str_message += f"Title field is empty. "
            boo_total_check = False
        if str_media_type not in ['audio', 'video']:
            str_message += f"Invalid media_type: {str_media_type}. " 
            boo_total_check = False
        if str_media_type == 'video':
            try:
                str_max_width = int(str_max_width)
                if str_max_width <= 0:
                    str_message += f"Invalid max_width: {str_max_width}. "
                    boo_total_check = False
            except ValueError:
                str_message += f"Invalid max_width: {str_max_width}. "
                boo_total_check = False
        if not str_url:
            str_message += f"URL is empty. "
            boo_total_check = False
        else:
            if not fn_is_url_reachable(str_url):
                str_message += f"URL is not reachable. "
                boo_total_check = False
        if not boo_total_check:
            fn_send_message(str_message)
        return boo_total_check
    except Exception as ex:
        fn_send_message(str(ex))

def fn_mt_validate_csv(path):
    class_stop_event.clear()
    try:
        fn_send_message("Performing CSV validation. Each URL is being tested as well. Please wait.")
        if not path or not os.path.exists(path):
            fn_send_message("Invalid path or file does not exist.")
            return False
        panda_table = fn_read_table(path)
        list_table_rows = panda_table.values.tolist()
        list_headers = panda_table.columns.to_list()
        if list_headers != arr_csv_field_names:
            fn_send_message(f"Invalid headers. Expected: {arr_csv_field_names}, saw {list_headers}")
            return False
        
        bool_total_check = True
        int_list_length = len(list_table_rows)
        fn_send_message(f'{int_list_length} rows are being validated')
        int_message_index = int(time.time() * 1000)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(fn_validate_row, row, int_list_index, int_list_length, int_message_index): int_list_index
                for int_list_index, row in enumerate(list_table_rows, start=1)
            }
            for future in concurrent.futures.as_completed(futures):
                if class_stop_event.is_set():  
                    fn_send_message("Operation stopped by user.")
                    executor.shutdown(wait=False)
                    return False                    
                bool_is_row_valid = future.result()                    
                if not bool_is_row_valid:
                    bool_total_check = False
        if bool_total_check:
            _, file_extension = os.path.splitext(path)
            fn_send_message(f"{file_extension} file is valid.")          
        return bool_total_check
    except Exception as ex:
        fn_send_message(str(ex))

def fn_upload_csv(e):
    global str_csv_path
    if bool_is_downloading:
        return
    uploaded_file = filedialog.askopenfilename( 
        initialdir = "/", 
        title = "OCDownloader: Select a CSV File", 
        filetypes = [("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls")]
    )
    if(fn_mt_validate_csv(uploaded_file)): 
        str_csv_path = uploaded_file
        fn_save_settings()

def abort(e):
    class_stop_event.set()

def fn_check_working_csv():
    try:
        if(str_csv_path and os.path.exists(str_csv_path)):
            arr_csv_working_path = str_csv_path.split('\\')
            fn_send_message(f'{arr_csv_working_path[-1]} was found from a previous session and auto-loaded.')
    except Exception as ex:
        fn_send_message(str(ex))

def fn_download_file(list_row, int_row_index, int_row_count, int_message_index):
    sub_folder = list_row[0]
    artist = list_row [1]
    title = list_row [2]
    str_queue_pos = f'{int_row_index}/{int_row_count}'
    str_message_prefix = f'[{str_queue_pos} {sub_folder}: {artist} - {title}]: '        
    str_message_index = str(int_message_index)
    try:    
        str_downloads_path = os.path.join(str_program_path, 'Downloads')
        str_ffmpeg_path = os.path.join(str_tools_path, 'ffmpeg.exe')        
        if sub_folder:
            sub_folder_parts = re.split(r'[\\\/]', sub_folder)
            sub_folder = os.sep.join(sub_folder_parts)
        media_type = list_row[3]
        max_width_in_pixels = int(list_row[4]) if media_type == 'video' else 0
        url = list_row[5]        
        if class_stop_event.is_set():
            fn_send_message(f"{str_message_prefix} Skipped before subfolder creation.", str_message_index)   
            return
        sub_folder_path = os.path.join(str_downloads_path, sub_folder)
        os.makedirs(sub_folder_path, exist_ok=True)

        def fn_yt_dlp_progress_hook(d):
            if 'status' in d:
                message = f"[{d['status'].capitalize()}] {d.get('filename', 'Unknown file')}"
                modified_message = f'{str_message_prefix}' + message  # Append custom string
                fn_send_message(modified_message, str_message_index)  # Send modified message

        class class_yt_dlp_CustomLogger:
            def debug(self, message):
                self._log(message)            
            def info(self, message):
                self._log(message)
            def warning(self, message):
                self._log(message)
            def error(self, message):
                self._log(message)
            def _log(self, message):
                modified_message =  f'{str_message_prefix} ' + message
                fn_send_message(modified_message, str_message_index)

        final_filename = f"{artist} - {title}" 
        ydl_opts_check = {
            'ffmpeg_location': str_ffmpeg_path,
            'quiet': True,
        }

        with ytdl.YoutubeDL(ydl_opts_check) as ydl:
        
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            best_format = None
            lowest_width_threshold = 80 * max_width_in_pixels
            str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp3")
            
            if media_type == 'video':
                str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp4")
            
            if os.path.exists(str_final_path_to_check):
                fn_send_message(f'{str_message_prefix} Aborted. File exists', int_message_index)
                return

            if media_type == 'video':
                fn_send_message(f'{str_message_prefix} Looking for stream', int_message_index)
                best_format = None
                for format in formats:
                    if format.get('ext') == 'mp4' and format.get('vcodec') != 'none' and format.get('acodec') != 'none':
                        if lowest_width_threshold < format.get('width', 0) <= max_width_in_pixels:
                            if best_format is None or format.get('width') > best_format.get('width'):
                                best_format = format
            if best_format:
                fn_send_message(f'{str_message_prefix} Found format: {best_format["ext"]}', int_message_index)
                ydl_opts = { 
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'format': best_format['format_id'],
                    'quiet': True,
                    'progress_hooks': [fn_yt_dlp_progress_hook],  # Hook for progress updates
                    'logger': class_yt_dlp_CustomLogger(),
                }
                if class_stop_event.is_set():
                    fn_send_message(f"{str_message_prefix} Skipped before file download", int_message_index)
                    return
                fn_send_message(f'{str_message_prefix} Downloading', int_message_index) 
             
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])            
            else:
                ydl_opts = {
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),
                    'ffmpeg_location': str_ffmpeg_path,
                    'no_warnings': True,
                    'overwrites': True,
                    'progress_hooks': [fn_yt_dlp_progress_hook],  # Hook for progress updates
                    'logger': class_yt_dlp_CustomLogger(),
                }
                if media_type == 'audio':
                    ydl_opts.update({'format': 'bestaudio/best'})
                elif media_type == 'video':
                    format_string = f'bestvideo[width<={max_width_in_pixels}]+bestaudio/best'
                    ydl_opts.update({'format': format_string})
                else:
                    raise ValueError("Invalid media type. Choose 'audio' or 'video'.")                
                if class_stop_event.is_set():
                    fn_send_message(f"{str_message_prefix} Skipped before file download", int_message_index)
                    return                
                if media_type == 'video':
                    fn_send_message(f'{str_message_prefix} Downloading A/V Stream to Merge', int_message_index)
                else:
                    fn_send_message(f'{str_message_prefix} Downloading Audio Stream', int_message_index)
                with ytdl.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.download([url])
                    fn_send_message(f'{str_message_prefix} Downloading Audio Stream {str(result)}', int_message_index)
                    if result == 0 and media_type == 'audio':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_message(f'{str_message_prefix} Downloaded File Extension is {str_file_extension}', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_message(f'{str_message_prefix} Converting to MP3', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file, '-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp3")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"{str_message_prefix} Converting {int(progress)}%",int_message_index)
                        os.remove(downloaded_file)
                    elif result == 0 and media_type == 'video':
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        fn_send_message(f'{str_message_prefix} Downloaded File Extension is {str_file_extension}]', int_message_index) 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        fn_send_message(f'{str_message_prefix} Converting to MP4', int_message_index)
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file,'-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp4")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            fn_send_message(f"{str_message_prefix} Converting {int(progress)}%",int_message_index)                           
                        os.remove(downloaded_file)
                    fn_send_message(f'{str_message_prefix} Done', int_message_index) 
        return True
    except Exception as ex:
        fn_send_message(str(ex))

def fn_mt_download_from_csv(e):
    global bool_is_downloading
    class_stop_event.clear()
    """
    Handles multi-threaded downloading from a CSV file.

    Preceding steps before starting multi-threading:
    
    1. **Validate the CSV file**  
       - Calls `fn_mt_validate_csv(str_csv_path)`, which checks if the CSV format is correct.  
       - If validation fails, sends a message to the GUI and stops execution.
    
    2. **Open the CSV file**  
       - Reads the file using `csv.reader(file)`.  
       - Extracts headers and ensures the structure matches expectations.  
       - Converts all rows into a list for processing.

    3. **Count and notify total downloads**  
       - Counts the number of rows in the CSV.  
       - Sends a message to the GUI about the number of items being downloaded.

    Once these steps are complete, the function proceeds to launch multiple downloads
    using `concurrent.futures.ThreadPoolExecutor()`.
    """   
    try:
        if bool_is_downloading:
            return
        
        bool_is_downloading = True
        if not fn_mt_validate_csv(str_csv_path):
            fn_send_message('Download Cancelled Due To Validation Issues.')
            return

        panda_table = fn_read_table(str_csv_path)
        list_table_rows = panda_table.values.tolist()
        list_headers = panda_table.columns.to_list()
        int_list_length = len(list_table_rows)
        fn_send_message(f'Downloading {int_list_length} items.')           
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(fn_download_file, list_row, int_row_index, int_list_length, int_message_id): int_row_index
                for int_row_index, list_row in enumerate(list_table_rows, start=1)
                if (int_message_id := str(int(time.time() * 1000)) + str(random.randrange(100000, 1000000)))
            }

            for future in concurrent.futures.as_completed(futures):
                if class_stop_event.is_set():
                    fn_send_message("Operation stopped by user.")
                    executor.shutdown(wait=False)  # Stop all downloads immediately
                    return                
                result = future.result()  # Ensure completed downloads are processed

        fn_send_message("Download and conversion complete.")
        bool_is_downloading = False
    except Exception as ex:
        fn_send_message(str(ex))

def fn_terminate_processes():
    target_processes = ["ffmpeg.exe"]
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            if proc.info["name"].lower() in target_processes:
                fn_send_message(f"Terminating {proc.info['name']} (PID: {proc.pid})")
                proc.terminate()
                proc.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            if proc.info["name"].lower() in target_processes:
                fn_send_message(f"Forcing kill on {proc.info['name']} (PID: {proc.pid})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

bool_is_closing = False  # Global flag to prevent multiple executions

def fn_on_closing():
    """
    Handles window close event in PyWebView, ensuring proper cleanup before exiting.

    Findings on how PyWebView handles events:
    - The `closing` event can **fire multiple times** before the window actually closes.
    - Blocking operations like `time.sleep()` in the main thread cause the UI to **freeze (Not Responding)**.
    - WebView does **not automatically close the window** if `closing` returns `False`, requiring manual closure.

    Solution:
    - Uses `is_closing` to **prevent multiple triggers** of the close event.
    - Runs cleanup in a separate thread to **avoid UI freeze**.
    - Calls `obj_window.destroy()` to **manually close the window** after cleanup.
    - Uses `os._exit(0)` to **ensure all processes terminate cleanly**.
    """
    global bool_is_closing
    if bool_is_closing:
        return False  # Prevent multiple triggers
    bool_is_closing = True  # Set flag to prevent re-entry
    def cleanup():
        """
        Performs cleanup before closing the application.
        - Sends a message to the UI.
        - Waits to allow the message to be processed.
        - Terminates processes and closes the window.
        """
        fn_send_message("Closing application and terminating processes...")
        time.sleep(1)  # Allow time for message to be sent
        fn_terminate_processes()
        obj_window.destroy()  # Manually close the window
        os._exit(0)  # Ensure full shutdown
    threading.Thread(target=cleanup, daemon=True).start()  # Run cleanup in background
    return True  # Allow the window to close after cleanup starts

def fn_bind(obj_window):
    fn_load_settings()
    fn_send_message('Initializing...')
    fn_check_working_csv()
    fn_send_message('Initialized.')
    btn_create_csv = obj_window.dom.get_element('#btn_cr_csv')
    btn_create_csv.on('click', lambda e: fn_create_csv(e))  
    btn_upload_csv = obj_window.dom.get_element('#btn_ul_csv')
    btn_upload_csv.on('click', lambda e: fn_upload_csv(e))
    btn_download_from_csv = obj_window.dom.get_element('#btn_dl_csv')
    btn_download_from_csv.on('click', lambda e: fn_mt_download_from_csv(e))    
    btn_abort = obj_window.dom.get_element('#btn_abrt')
    btn_abort.on('click', lambda e: abort(e))
    obj_window.events.closing += lambda: fn_on_closing()
    return

if __name__ == '__main__':
    fn_get_paths()
    str_html_path = os.path.join(str_tools_path, 'home.html')
    obj_window = webview.create_window(
        'OCDownloader',
        str_html_path,
        width=800,
        height=800,
        )    
    webview.start(fn_bind, obj_window)