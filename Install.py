import getpass
import os
USER_NAME = getpass.getuser()

cwd = os.getcwd()
def add_to_startup(file_path):
    vbs_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % USER_NAME
    bat_path = cwd + "\\open.bat"
    with open(bat_path, "w+") as bat_file:
        bat_file.write(f'python {file_path}')
    with open(vbs_path + '\\' + "open.vbs", "w+") as vbs_file:
        vbs_file.writelines('Set WshShell = CreateObject("WScript.Shell")\n')
        vbs_file.write(f'WshShell.Run chr(34) & "{bat_path}" & Chr(34), 0\n')
        vbs_file.write('Set WshShell = Nothing')



add_to_startup(cwd + "\\Autostart.py " + cwd + "\\UI_Window.py")