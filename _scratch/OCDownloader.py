import webview
import sys
import os
import json

obj_window = None
str_program_path = None
str_tools_path = None

def fn_send_message(str, str_id=None):
    try:
        if obj_window:
            str_json = json.dumps(str)
            if str_id is None:
                str_id = ''
            str_id_json = json.dumps(str_id)
            obj_window.evaluate_js(f'fn_send_message({str_json}, {str_id_json})')        
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
            str_tools_path = os.path.join(str_program_path, 'tools')       
    except Exception as ex:
        fn_send_message(str(ex))

def fn_create_csv(e):
    fn_send_message('test')

def fn_bind(obj_window):
    btn_cr_csv = obj_window.dom.get_element('#btn_cr_csv')
    btn_cr_csv.on('click', lambda e: fn_create_csv(e))  

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