import os  # Importing the os module for interacting with the file system
import sys  # Importing the sys module to access system-specific parameters
import webview  # Importing webview for creating a GUI window to interact with web content
import json  # Importing json to work with JSON data
import csv  # Importing csv to handle CSV files
from tkinter import filedialog  # Importing filedialog to open file selection dialogs
import requests  # Importing requests to make HTTP requests
import re  # Importing re for regular expressions
import yt_dlp as ytdl  # Importing yt_dlp for downloading content from the internet (like YouTube)
import psutil
from ffmpeg_progress_yield import FfmpegProgress
import subprocess
from subprocess import CREATE_NO_WINDOW

window = None  # Webview window object
str_tools_path = None  # Path for bundled files in .exe mode or script root directory
str_program_path = None  # Root directory of .py or .exe
str_config_name = 'config.json'  # Retained configuration filename
str_csv_name = 'OCDList.csv'  # Name of the generated csv
arr_csv_field_names = ['sub_folder','artist','title','media_type_audio_or_video','max_width_in_pixels', 'url']  # csv header list
int_row_count = 0  # Rows within the csv
int_current_row = 0  # Current Row in queue
bool_is_abort_requested = False  # Flag to check if abort was requested
str_os_sep = os.sep

str_csv_path = None  # Path of the uploaded csv

def send_message(str):  # Function to send a message to the webview window
    safe_str = json.dumps(str)  # Safely encode string as JSON
    if(window):  # If window exists
        window.evaluate_js(f'send_message({safe_str})')  # Send the message to the JavaScript function in the webview

def send_queue(str):  # Function to send a queue message to the webview window
    safe_str = json.dumps(str)  # Safely encode string as JSON
    if(window):  # If window exists
        window.evaluate_js(f'send_queue({safe_str})')  # Send the queue message to the JavaScript function in the webview

class StreamRedirector:  # Class to redirect output streams
    def write(self, message):  # Function to write the message to the webview
        if message.strip():  # If message is not empty
            send_message(message.strip())  # Send the stripped message
    def flush(self):  # Flush function for the stream (no implementation required)
        pass
sys.stdout = StreamRedirector()  # Redirect standard output to the StreamRedirector class
sys.stderr = StreamRedirector()  # Redirect standard error to the StreamRedirector class

def get_paths(): # Resolve program paths to be used in locating files
    global str_program_path, str_tools_path
    if getattr(sys, 'frozen', False):  # Check if running in bundled mode
            str_program_path = os.path.abspath(os.path.dirname(sys.executable))
            str_tools_path = os.path.join(str_program_path,'_internal','tools') 
    else:  # If running from source code
            str_program_path = os.path.abspath(os.path.dirname(__file__))
            str_tools_path = os.path.join(str_program_path,'tools') 

def save_settings():  # Function to save settings in a JSON file
    dictionary = {'str_csv_path': f'{str_csv_path}'}  # Dictionary of settings to save
    settings_path = os.path.join(str_program_path, str_config_name)  # Path for config.json
    with open(settings_path, 'w') as outfile:  # Open the file for writing
        json.dump(dictionary, outfile)  # Write the settings as JSON

def load_settings():  # Function to load settings from config.json
    global str_csv_path  # Declare global variable
    config_path = os.path.join(str_program_path, str_config_name)  # Path for config.json
    if(os.path.exists(config_path)):  # If the config file exists
        with open(config_path, 'r') as openfile:  # Open the file for reading
            json_object = json.load(openfile)  # Load JSON data from the file
            str_csv_path = json_object['str_csv_path']  # Set the CSV path from the loaded settings
    else:
        save_settings()  # If no config file, save default settings

def create_csv(e):  # Function to create a default CSV file
    try:
        default_csv_path = os.path.join(str_program_path, str_csv_name)  # Path for the CSV file
        if(os.path.exists(default_csv_path)):  # If the CSV file already exists
            send_message(f'{str_csv_name} already exists in the parent directory. Operation aborted.')  # Abort operation
        else:  # If the file doesn't exist
            with open(default_csv_path, 'w', newline = '') as csvfile:  # Open the file for writing
                writer = csv.DictWriter(csvfile, fieldnames = arr_csv_field_names)  # Create CSV writer with header
                writer.writeheader()  # Write header to CSV
            send_message(f'{str_csv_name} created succesfully.')  # Notify success
    except Exception as ex:  # If there is any error
        send_message(str(ex))  # Send the error message
        raise

def is_url_reachable(url):  # Function to check if a URL is reachable
    try:
        response = requests.get(url)  # Send GET request to the URL
        return response.status_code == 200  # Return True if status code is 200 (OK)
    except requests.exceptions.RequestException:  # If there is a request exception
        return False  # Return False if URL is unreachable

def validate_row(row, int_row_count):  # Function to validate a single row of the CSV
    sub_folder, artist, title, media_type, max_width, url = row  # Extract values from row
    if sub_folder and not re.match(r'^[\w\-.\\/]+$', sub_folder):  # Validate sub_folder format using regex, now allowing both slashes
        send_message(f"Invalid sub_folder format in row {int_row_count}: {sub_folder}")  # Invalid sub_folder
        return False  # Return False if invalid
    if not title:  # If title is empty
        send_message(f"Title field is empty in row {int_row_count}.")  # Notify empty title
        return False  # Return False if invalid
    if media_type not in ['audio', 'video']:  # If media_type is not 'audio' or 'video'
        send_message(f"Invalid media_type in row {int_row_count}: {media_type}")  # Invalid media_type
        return False  # Return False if invalid
    if media_type == 'video':  # If media type is video
        try:
            max_width = int(max_width)  # Convert max_width to integer
            if max_width <= 0:  # If max_width is not positive
                send_message(f"Invalid max_width in row {int_row_count}: {max_width}")  # Invalid max_width
                return False  # Return False if invalid
        except ValueError:  # If max_width cannot be converted to integer
            send_message(f"Invalid max_width in row {int_row_count}: {max_width}")  # Invalid max_width
            return False  # Return False if invalid
    if not url:  # If URL is empty
        send_message(f"URL is empty in row {int_row_count}.")  # Notify empty URL
        return False  # Return False if invalid
    if not is_url_reachable(url):  # If the URL is not reachable
        send_message(f"URL is not reachable in row {int_row_count}.")  # Notify unreachable URL
        return False  # Return False if invalid
    return True  # Return True if all validations pass

def validate_csv(path):  # Function to validate the entire CSV file
    try:
        if path:
            if os.path.exists(path):
                global int_row_count  # Declare global variable
                with open(path, 'r', newline='', encoding='utf-8') as upfile:  # Open the CSV file for reading
                    reader = csv.reader(upfile)  # Create CSV reader
                    headers = next(reader)  # Read the headers of the CSV
                    if headers != arr_csv_field_names:  # If headers do not match expected
                        send_message(f"Invalid headers. The file should only contain these headers: {arr_csv_field_names}")  # Notify invalid headers
                        return False  # Return False if headers are invalid
                    int_row_count = 0  # Initialize row count
                    bool_total_check = True  # Flag for checking all rows
                    for row in reader:  # Iterate over rows in the CSV
                        int_row_count += 1  # Increment row count
                        if not validate_row(row, int_row_count):  # Validate each row
                            bool_total_check = False  # Set flag to False if any row is invalid
                    send_message(f'This file has {int_row_count} rows.')  # Notify total rows in the file
                    if bool_total_check:  # If all rows are valid
                        send_message('The headers and rows have been validated.')  # Notify success
                    return bool_total_check  # Return validation status
            else:
                send_message('CSV not found.')
        else:
            send_message('CSV not found.')    
    except Exception as ex:  # If there is any error
        send_message(str(ex))  # Send the error message
        return False  # Return False if error occurs

def upload_csv(e):  # Function to upload a CSV file
    global str_csv_path  # Declare global variable
    uploaded_file = filedialog.askopenfilename(  # Open file dialog to select CSV
        initialdir = "/",  # Initial directory
        title = "OCDownloader: Select a CSV File",  # Dialog title
        filetypes = [("CSV files", "*.csv")]  # Filter for CSV files
    )
    if(validate_csv(uploaded_file)):  # If the CSV is valid
        str_csv_path = uploaded_file  # Set the CSV path
        save_settings()  # Save settings with the new CSV path

def abort(e):  # Function to abort the operation
    global bool_is_abort_requested
    bool_is_abort_requested = True
    send_message('Aborting after last ongoing download.')  # Notify abort
    send_queue('Aborting after last ongoing download.')  # Send abort message to the queue

def download_file(row):  # Function to download a file based on the row data from the CSV
    try:
        str_downloads_path = os.path.join(str_program_path, 'Downloads')  # Path for the Downloads directory
        str_ffmpeg_path = os.path.join(str_tools_path, 'ffmpeg.exe')  # Path for ffmpeg executable
        sub_folder = row['sub_folder']  # Get sub-folder from the row
        if sub_folder:  # If not empty adjust so that it uses proper dir slashing
            sub_folder_parts = re.split(r'[\\\/]', sub_folder)
            sub_folder = os.sep.join(sub_folder_parts)
        artist = row['artist']  # Get artist from the row
        title = row['title']  # Get title from the row
        media_type = row['media_type_audio_or_video']  # Get media type (audio/video) from the row
        max_width_in_pixels = int(row['max_width_in_pixels']) if media_type == 'video' else 0  # Get max width for video
        url = row['url']  # Get URL from the row
        if sub_folder:
            sub_folder_path = os.path.join(str_downloads_path, sub_folder)  # Create path for the sub-folder
        else:
            sub_folder_path = str_downloads_path
        os.makedirs(sub_folder_path, exist_ok=True)  # Create the sub-folder if it doesn't exist
        final_filename = f"{artist} - {title}" 
        ydl_opts_check = {  # Options for yt-dlp (check mode without downloading)
            'ffmpeg_location': str_ffmpeg_path,  # Set the location of ffmpeg
            'quiet': True,  # Quiet mode (no output)
        }
        send_queue(f'[{int_current_row}/{int_row_count}] {sub_folder}: {artist} - {title}')  # Send progress message
        with ytdl.YoutubeDL(ydl_opts_check) as ydl:  # Create yt-dlp instance with check options
            info_dict = ydl.extract_info(url, download=False)  # Extract information about the URL without downloading
            formats = info_dict.get('formats', [])  # Get the list of available formats
            best_format = None  # Variable to hold the best format for video
            lowest_width_threshold = 80 * max_width_in_pixels  # Calculate threshold for video width

            str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp3")
            if media_type == 'video':
                str_final_path_to_check = os.path.join(sub_folder_path, f"{final_filename}.mp4")
            if os.path.exists(str_final_path_to_check):
                send_message('Download aborted: {str_final_path_to_check} exists.')
                return
            if media_type == 'video':  # If media type is video
                send_message('Looking for best video format.')  # Notify searching for video format
                best_format = None  # Initialize best format variable
                for format in formats:  # Iterate through available formats
                    if format.get('ext') == 'mp4' and format.get('vcodec') != 'none' and format.get('acodec') != 'none':  # If format is mp4 and has video/audio codecs
                        if lowest_width_threshold < format.get('width', 0) <= max_width_in_pixels:  # If format width is within the max width range
                            if best_format is None or format.get('width') > best_format.get('width'):  # Choose the best format
                                best_format = format  # Set the best format
            if best_format:  # If a best format is found
                send_message(f"Found suitable format: {best_format['ext']}")  # Notify suitable format found
                ydl_opts = {  # Set download options for yt-dlp
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),  # Set the output template
                    'ffmpeg_location': str_ffmpeg_path,  # Set ffmpeg location
                    'no_warnings': True,  # Disable warnings
                    'format': best_format['format_id'],  # Set the chosen format
                    'quiet': True,  # Quiet mode
                }
                send_message(f"Starting download: {sub_folder}: {artist} - {title}")  # Notify start of download
                send_message('[enable_spinner]')  # Enable spinner (loading indicator)
                with ytdl.YoutubeDL(ydl_opts) as ydl:  # Create yt-dlp instance with the final download options
                    ydl.download([url])  # Start downloading
            else:  # If no suitable format is found
                if media_type == 'video':  # If media type is video
                    send_message('No suitable video+audio stream found. Downloading separate audio and video.')  # Notify separate download
                else:  # If media type is audio
                    send_message('Downloading audio stream.')  # Notify audio download
                ydl_opts = {  # Set download options for yt-dlp
                    'outtmpl': os.path.join(sub_folder_path, f"{final_filename}.%(ext)s"),  # Set the output template
                    'ffmpeg_location': str_ffmpeg_path,  # Set ffmpeg location
                    'no_warnings': True,  # Disable warnings
                    'overwrites': True,  # Allow overwriting of files
                }
                if media_type == 'audio':  # If media type is audio
                    ydl_opts.update({'format': 'bestaudio/best'})
                elif media_type == 'video':  # If media type is video
                    format_string = f'bestvideo[width<={max_width_in_pixels}]+bestaudio/best'  # Set format string for video and audio
                    ydl_opts.update({'format': format_string})  # Update format options
                else:  # If media type is invalid
                    raise ValueError("Invalid media type. Choose 'audio' or 'video'.")  # Raise error for invalid media type
                send_message(f"Starting download: {sub_folder}: {artist} - {title}")  # Notify start of download
                send_message('[enable_spinner]')  # Enable spinner (loading indicator)
                with ytdl.YoutubeDL(ydl_opts) as ydl:  # Create yt-dlp instance with the final download options
                    result = ydl.download([url])  # Start downloading
                    if result == 0 and media_type == 'audio':  # Convert to MP3
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)  # This will give the complete path with extension
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        send_message(f'Downloaded file ext is: {str_file_extension}') 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        send_message(f"Converting to MP3: {downloaded_file}")
                        #subprocess.run([str_ffmpeg_path, '-i', downloaded_file, '-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp3")])
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file, '-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp3")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)  # Remove the original file after conversion
                    elif result == 0 and media_type == 'video':  # Convert to MP4
                        info_dict = ydl.extract_info(url, download=False)
                        str_file_path = ydl.prepare_filename(info_dict)  # This will give the complete path with extension
                        str_file_extension = os.path.splitext(str_file_path)[1][1:]
                        send_message(f'Downloaded file ext is: {str_file_extension}') 
                        downloaded_file = os.path.join(sub_folder_path, f"{final_filename}.{str_file_extension}")
                        send_message(f"Converting to MP4: {downloaded_file}")
                        #subprocess.run([str_ffmpeg_path, '-i', downloaded_file,'-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp4")])
                        ffmpeg_cmd = [str_ffmpeg_path, '-i', downloaded_file,'-progress', 'pipe:1','-y', os.path.join(sub_folder_path, f"{final_filename}.mp4")]
                        ff = FfmpegProgress(ffmpeg_cmd)
                        for progress in ff.run_command_with_progress({"creationflags":CREATE_NO_WINDOW}):
                            send_message(f"[Conversion Progress]: {int(progress)}%")
                        os.remove(downloaded_file)  # Remove the original file after conversion
    except Exception as ex:  # If there is any error
        send_message(str(ex))  # Send the error message

def download_from_csv(e):  # Function to download files based on CSV data
    global int_current_row  # Declare global variable for row count
    global int_row_count
    global bool_is_abort_requested  # Declare global variable for abort flag
    try:
        int_row_count = 0
        int_current_row = 0        
        send_message('Running last-minute CSV validation.')  # Notify CSV validation
        bool_is_csv_rows_ok = validate_csv(str_csv_path)  # Validate the CSV file
        if not bool_is_csv_rows_ok:  # If CSV is invalid
            send_message("CSV rows are invalid.")  # Notify invalid rows
            return  # Stop further execution
        send_queue(f'Total files to download: {int_row_count}')  # Send total number of files to download
        with open(str_csv_path, mode='r', newline='') as file:  # Open the CSV file for reading
            csv_reader = csv.DictReader(file)  # Create a CSV reader
            for row in csv_reader:  # Iterate over rows in the CSV
                try:
                    if bool_is_abort_requested == False:  # If not abort requested
                        int_current_row += 1  # Increment current row count
                        download_file(row)  # Download the file based on row data
                    else:
                        bool_is_abort_requested = False  # Reset abort flag
                        return  # Return if abort is requested
                except Exception as ex:  # If there is any error
                    send_message(str(ex))  # Send the error message
                    continue  # Continue with the next row
        send_message('[disable_spinner]')  # Disable spinner (loading indicator)
        send_message("Download and conversion complete.")  # Notify download complete
        send_queue("Download and conversion complete.")  # Send download completion message to the queue
    except Exception as ex:  # If there is any error
        send_message(str(ex))  # Send the error message

def check_working_csv():  # Function to check if the CSV was found and loaded from previous session
    if(str_csv_path and os.path.exists(str_csv_path)):  # If CSV path is set and file exists
        arr_csv_working_path = str_csv_path.split('\\')  # Split the path for display
        send_message(f'{arr_csv_working_path[-1]} was found from a previous session and auto-loaded.')  # Notify CSV auto-load

def terminate_ffmpeg(): # Function to terminate ffmpeg.exe
    for proc in psutil.process_iter(['pid', 'name']):
        if 'ffmpeg' in proc.info['name'].lower():  # Check for ffmpeg process
            try:
                proc.terminate()  # Terminate the process
                proc.wait()  # Wait for the process to finish termination
                print(f"Terminated ffmpeg process with PID: {proc.info['pid']}")
            except psutil.NoSuchProcess:
                pass  # In case the process is already gone

def on_window_closed(): # Terminate ffmpeg.exe on window closed
    terminate_ffmpeg()

def bind(window): # Bind python functions to events of front-end elements
    try:
        load_settings()  # Load settings from the config file
        send_message(f'Initializing...')  # Notify initialization
        check_working_csv()  # Check if a CSV file was loaded from a previous session
        send_message(f'Initialized.')  # Notify initialization
        btn_create_csv = window.dom.get_element('#btn_create_csv')  # Get the create CSV button element
        btn_create_csv.on('click', lambda e: create_csv(e))  # Bind click event to create CSV function
        btn_upload_csv = window.dom.get_element('#btn_upload_csv')  # Get the upload CSV button element
        btn_upload_csv.on('click', lambda e: upload_csv(e))  # Bind click event to upload CSV function
        btn_abort = window.dom.get_element('#btn_abort')  # Get the abort button element
        btn_abort.on('click', lambda e: abort(e))  # Bind click event to abort function
        btn_download_from_csv = window.dom.get_element('#btn_download_from_csv')  # Get the download button element
        btn_download_from_csv.on('click', lambda e: download_from_csv(e))  # Bind click event to download CSV function
    except Exception as ex:  # If there is any error
        send_message(str(ex))  # Send the error message

if __name__ == '__main__':
    get_paths()
    str_html_path = os.path.join(str_tools_path,'home.html')
    window = webview.create_window('OCDownloader', str_html_path, width=800, height=800)
    window.events.closing += on_window_closed 
    webview.start(bind, window)