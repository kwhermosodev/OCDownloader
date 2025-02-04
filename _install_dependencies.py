import subprocess
import sys

libraries = [
    "pyinstaller",
    "pywebview",
    "pythonnet"
    #"requests",
    #"yt-dlp",
    #"psutil",
]

def install_libraries(library_list):
    for library in library_list:
        try:
            print(f"Installing {library}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])
            print(f"{library} installed successfully!")
        except subprocess.CalledProcessError:
            print(f"Failed to install {library}.")

if __name__ == "__main__":
    install_libraries(libraries)