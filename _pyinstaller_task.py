import os
import subprocess
import shutil
import zipfile
import sys

str_project_name = 'OCDownloader'
str_program_path = os.path.abspath(os.path.dirname(__file__))
str_info_js_path = os.path.join(str_program_path,'tools','home.js')

def get_python_version():
    version = sys.version.split()[0]  # Get the first part of the version string
    return f"python - {version}"

def get_pip_list():
    result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True)
    pip_list = result.stdout.splitlines()[2:]  # Skip the header (first 2 lines)
    return [f"{pkg.split()[0]} - {pkg.split()[1]}" for pkg in pip_list]

def update_home_js(str_info_js_path):
    python_version = get_python_version()
    pip_list = get_pip_list()
    
    # Read the current content of the JS file
    with open(str_info_js_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Find where to insert the version and pip list
    start_index = content.find('arr_libraries = [') + len('arr_libraries = [')
    end_index = content.find('];', start_index)
    
    if start_index != -1 and end_index != -1:
        # Update the array with the new Python version and pip list
        pip_list_formatted = '", "'.join(pip_list)
        updated_content = (content[:start_index] + f'"{python_version}", "{pip_list_formatted}"' + content[end_index:])
        
        # Write the updated content back to the file
        with open(str_info_js_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

def bundle_project(str_project_name):
    
    str_parent_path = os.path.dirname(os.path.abspath(__file__))
    str_pyinstraller_path = os.path.join(str_parent_path,'_venv','Scripts', 'pyinstaller.exe')
    str_bundle_path =  os.path.join(str_parent_path, 'bundle')
    str_dist_onedir_path = os.path.join(str_bundle_path,'onedir','dist')
    str_dist_onefile_path = os.path.join(str_bundle_path,'onefile','dist')
    str_build_onedir_path = os.path.join(str_bundle_path,'onedir','build')
    str_build_onefile_path = os.path.join(str_bundle_path,'onefile','build')
    str_data_path = os.path.join(str_parent_path, 'tools') + ';tools'
    str_icon_path = os.path.join(str_parent_path,'tools','ico.ico')
    str_script_path = os.path.join(str_parent_path, str_project_name + '.py')

    pyinstaller_cmd_onedir = [
        f'{str_pyinstraller_path}',
        '--onefile',
        '--noconsole',
        '--windowed',
        f'--distpath={str_dist_onedir_path}',
        f'--workpath={str_build_onedir_path}',
        f'--specpath={str_bundle_path}',
        f'--add-data={str_data_path}',
        f'--icon={str_icon_path}'
    ]

    pyinstaller_cmd_onefile = [
        f'{str_pyinstraller_path}',
        '--onefile',
        '--noconsole',
        '--windowed',
        f'--distpath={str_dist_onefile_path}',
        f'--workpath={str_build_onefile_path}',
        f'--specpath={str_bundle_path}',
        f'--add-data={str_data_path}',
        f'--icon={str_icon_path}'
    ]

    pyinstaller_cmd_onedir.append(str_script_path)
    pyinstaller_cmd_onefile.append(str_script_path)
    
    if(os.path.exists(str_bundle_path)):
        shutil.rmtree(str_bundle_path)
    
    subprocess.run(pyinstaller_cmd_onedir, check=True)
    subprocess.run(pyinstaller_cmd_onefile, check=True)

    print(f'{str_project_name} was bundled successfully at {str_bundle_path}')

    str_dist_project_path = os.path.join(str_dist_onedir_path,str_project_name)
    str_dist_output_zip = os.path.join(str_dist_onedir_path,str_project_name+'.zip')
    compress_folder(str_dist_project_path, str_dist_output_zip)

def compress_folder(input_folder, output_zip_file):
    with zipfile.ZipFile(output_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(input_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, input_folder)
                zipf.write(abs_path, rel_path)

if __name__ == "__main__":
    update_home_js(str_info_js_path)
    bundle_project(str_project_name)
