import webview
import os
import sys

str_program_path = None  # Root directory of .py or .exe
str_tools_path = None  # Path for bundled tools folder

# Resolve program paths to be used in locating files
def get_paths():
    global str_program_path, str_tools_path
    if getattr(sys, 'frozen', False):  # Check if running in bundled mode
            str_program_path = os.path.abspath(os.path.dirname(sys.executable))
            str_tools_path = os.path.join(str_program_path,'_internal','tools') 
    else:  # If running from source code
            str_program_path = os.path.abspath(os.path.dirname(__file__))
            str_tools_path = os.path.join(str_program_path,'tools') 

def bind(window):
    return

if __name__ == '__main__':
    get_paths()
    str_html_path = os.path.join(str_tools_path,'home.html')
    window = webview.create_window('OCDownloader', str_html_path, width=800, height=800)
    webview.start(bind, window)