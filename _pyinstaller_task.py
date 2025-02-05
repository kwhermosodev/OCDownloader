import os
import subprocess
import shutil
import py7zr

str_project_name = 'OCDownloader'

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
    str_dist_output_zip = os.path.join(str_dist_path,str_project_name+'.7z')
    compress_folder(str_dist_project_path, str_dist_output_zip)


import py7zr

def compress_folder(input_folder, output_7z_file):
    with py7zr.SevenZipFile(output_7z_file, 'w') as archive:
        archive.writeall(input_folder, arcname="")


if __name__ == "__main__":
    bundle_project(str_project_name)
