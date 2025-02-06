import os
import subprocess
import shutil
import zipfile
from bs4 import BeautifulSoup
import sys

str_project_name = 'OCDownloader'
str_program_path = os.path.abspath(os.path.dirname(__file__))
str_info_html_path = os.path.join(str_program_path,'tools','home.html')

def get_python_version():
    version = sys.version.split()[0]  # Get the first part of the version string
    return f"python - {version}"

def get_pip_list():
    """Returns a list of installed pip packages with their versions."""
    result = subprocess.run(['pip', 'list'], stdout=subprocess.PIPE, text=True)
    pip_list = result.stdout.splitlines()[2:]  # Skip the header
    return [f"{pkg.split()[0]} - {pkg.split()[1]}" for pkg in pip_list]

def update_html_with_lib_versions(str_path_to_html, str_ul_id):
    """Modifies the HTML file by adding a list of Python and pip library versions."""
    # Create the arr_lib array
    arr_lib = []
    arr_lib.append(get_python_version())  # Add Python version
    arr_lib.extend(get_pip_list())  # Add pip packages and versions

    # Open the HTML file and parse it with BeautifulSoup
    with open(str_path_to_html, 'r') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Find the <ul> tag by id and add the new <li> elements
    ul = soup.find('ul', id=str_ul_id)
    if ul:
        ul.clear()
        for lib_version in arr_lib:
            li = soup.new_tag('li')
            li.string = lib_version
            ul.append(li)
    else:
        print(f"Unordered list with id '{str_ul_id}' not found in the HTML.")

    # Save the modified HTML file
    with open(str_path_to_html, 'w') as file:
        file.write(str(soup))

def bundle_project(str_project_name):

    str_parent_path = os.path.dirname(os.path.abspath(__file__))
    #str_python_path = os.path.join(str_parent_path,'_venv','Scripts', 'python.exe')
    str_pyinstraller_path = os.path.join(str_parent_path,'_venv','Scripts', 'pyinstaller.exe')
    str_bundle_path =  os.path.join(str_parent_path, 'bundle')
    str_dist_path = os.path.join(str_bundle_path,'dist')
    str_build_path = os.path.join(str_bundle_path,'build')
    str_data_path = os.path.join(str_parent_path, 'tools') + ';tools'
    str_icon_path = os.path.join(str_parent_path,'tools','ico.ico')
    str_script_path = os.path.join(str_parent_path, str_project_name + '.py')

    # pyinstaller command as array
    pyinstaller_cmd = [
        #f'{str_python_path}',
        #'-m',
        f'{str_pyinstraller_path}',
        '--onedir',
        '--noconsole',
        '--windowed',
        #'--debug=all',
        f'--distpath={str_dist_path}',
        f'--workpath={str_build_path}',
        f'--specpath={str_bundle_path}',
        f'--add-data={str_data_path}',
        f'--icon={str_icon_path}'
    ]

    pyinstaller_cmd.append(str_script_path)

    if(os.path.exists(str_bundle_path)):
        shutil.rmtree(str_bundle_path) # remove old bundle   
    
    subprocess.run(pyinstaller_cmd, check=True)

    print(f'{str_project_name} was bundled successfully at {str_bundle_path}')

    str_dist_project_path = os.path.join(str_dist_path,str_project_name)
    str_dist_output_zip = os.path.join(str_dist_path,str_project_name+'.zip')
    compress_folder(str_dist_project_path, str_dist_output_zip)

def compress_folder(input_folder, output_zip_file):
    with zipfile.ZipFile(output_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(input_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, input_folder)
                zipf.write(abs_path, rel_path)

if __name__ == "__main__":
    update_html_with_lib_versions(str_info_html_path, 'ul_libraries')
    bundle_project(str_project_name)
