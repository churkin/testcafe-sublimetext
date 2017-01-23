import sys
import subprocess

def run(cmd):
    proc = None

    if sys.platform == 'win32':
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    elif sys.platform == 'darwin':
        # https://github.com/int3h/SublimeFixMacPath
        proc = subprocess.Popen(['/usr/bin/login -fqpl $USER $SHELL -l -c \'' + cmd + '\''], stdout=subprocess.PIPE,
                                shell=True)
    elif sys.platform == 'linux':
        # TODO:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    return proc


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
