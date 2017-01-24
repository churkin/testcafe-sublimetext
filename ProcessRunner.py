import sys
import subprocess


def run(cmd):
    if sys.platform == 'darwin' or sys.platform.startswith('linux'):
        # https://github.com/int3h/SublimeFixMacPath
        cmd = '$SHELL -l -i -c \'' + cmd + '\''

    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


def kill(proc):
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen('taskkill /PID ' + str(proc.pid), startupinfo=startupinfo)
    else:
        try:
            proc.terminate()
        except:
            # ST2 on the Mac raises exception
            pass
