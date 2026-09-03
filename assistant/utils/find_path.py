import os, subprocess, platform

def find_path(filename: str):
    if filename.endswith(".exe"):
        filename = filename[:-4]
        
    system = platform.system()

    if system == 'Windows':
        command = f"where {filename}.exe"
    else:
        command = f"which {filename}"

    try:
        result = subprocess.run(
            command, 
            capture_output= True, 
            text= True
        )

        list_path = result.stdout.split("\n")
        file = list_path[0].strip()
        
        if file != '':
            if os.path.exists(file):
                return file
    except:
        pass

    if system == "Windows":
        searching_dirs = [
            os.environ.get("APPDATA"),
            os.environ.get("LOCALAPPDATA"),
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.path.join(os.environ.get("SYSTEMROOT"), "System32"), 
            # "D:\\Applications"
        ]
        extentions = [".exe"]
    else:
        searching_dirs = [
            "/usr/bin",
            "/usr/local/bin",
            "/Applications",
            os.path.expanduser("~/Applications")
        ]
        extentions = ["", ".app"]
    
    for root_dir in searching_dirs:
        if not os.path.exists(root_dir):
            continue
        
        for current_path, inside_dirs, files in os.walk(root_dir):
            for file in files:
                for ext in extentions:
                    if file.lower() == filename.lower() + ext:
                        return os.path.join(current_path, file)
                    
            if current_path.count(os.sep) > root_dir.count(os.sep) + 3:
                inside_dirs.clear()
                
# apps = [
#     "python",
#     "telegram.exe",
#     "telegram",
#     "chrome",
#     "discord",
#     "code"
# ]

# for app in apps:
#     print(find_path(app))