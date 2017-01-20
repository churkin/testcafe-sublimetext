import sublime
import sublime_plugin
import os
import sys
import threading
import subprocess
import collections
import re

FIND_TEST_OR_FIXTURE_RE = '(^|;|\s+)fixture\s*(\(.+?\)|`.+?`)|(^|;|\s+)test\s*\(\s*(.+?)\s*,'
CLEANUP_TEST_OR_FIXTURE_NAME_RE = '(^\s*(\'|"|`))|((\'|"|`)\s*$)'


class AsyncProcess(object):
    def __init__(self, cmd, listener):
        self.listener = listener
        self.killed = False
        startupinfo = None

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc_env = os.environ.copy()
        for k, v in proc_env.items():
            proc_env[k] = os.path.expandvars(v)

        if sys.platform == 'win32':
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE, startupinfo=startupinfo,
                                         env=proc_env, shell=True)
        elif sys.platform == 'darwin':
            # https://github.com/int3h/SublimeFixMacPath
            self.proc = subprocess.Popen(['/usr/bin/login -fqpl $USER $SHELL -l -c \'' + cmd + '\''],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE, startupinfo=startupinfo,
                                         env=proc_env, shell=True)
        elif sys.platform == 'linux':
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE, startupinfo=startupinfo,
                                         env=proc_env, shell=True)
        else:
            self.proc = subprocess.Popen(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         stdin=subprocess.PIPE,
                                         startupinfo=startupinfo,
                                         env=proc_env)

        if self.proc.stdout:
            threading.Thread(target=self.read_stdout).start()

        if self.proc.stderr:
            threading.Thread(target=self.read_stderr).start()

    def kill(self):
        if not self.killed:
            self.killed = True
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen('taskkill /PID ' + str(self.proc.pid),
                                 startupinfo=startupinfo)
            else:
                self.proc.terminate()
            self.listener = None

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)

            if len(data) > 0:
                if self.listener:
                    self.listener.append_string(self, data)
            else:
                self.proc.stdout.close()
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)

            if len(data) > 0:
                if self.listener:
                    self.listener.append_string(self, data)
            else:
                self.proc.stderr.close()
                break


class TestCafeCommand(sublime_plugin.TextCommand):
    BLOCK_SIZE = 2 ** 14
    text_queue = collections.deque()
    text_queue_proc = None
    text_queue_lock = threading.Lock()

    previous_cmd = None
    proc = None

    def get_testcafe_cmd(self, test_code, file_name):
        match = None
        for match in re.finditer(FIND_TEST_OR_FIXTURE_RE, test_code, re.I | re.M):
            pass

        testcafe_cmd = file_name

        if match is None:
            return testcafe_cmd

        fixture_name = match.group(2)
        test_name = match.group(4)
        if fixture_name is not None:
            fixture_name = re.sub(CLEANUP_TEST_OR_FIXTURE_NAME_RE, '', fixture_name)
            return '{0} -f "{1}"'.format(testcafe_cmd, fixture_name)
        elif test_name is not None:
            test_name = re.sub(CLEANUP_TEST_OR_FIXTURE_NAME_RE, '', test_name)
            return '{0} -t "{1}"'.format(testcafe_cmd, test_name)

    def clear_output_view(self):
        self.output_view.set_read_only(False)
        self.output_view.erase(self.edit, sublime.Region(0, self.output_view.size()))
        self.output_view.set_read_only(True)

    def append_data_to_output_view(self, str):
        self.output_view.set_read_only(False)
        size = self.output_view.size()

        # SublimeText3
        self.output_view.run_command('append', {
            'characters': str,
            'force': True,
            'scroll_to_end': True})

        # SublimeText2
        if self.output_view.size() == size:
            self.output_view.insert(self.edit, self.output_view.size(), str)

        self.output_view.set_read_only(True)

    def run(self, edit, cmd=None, browser=''):
        self.edit = edit
        selection = self.view.sel()[0]
        line = self.view.line(selection.b)
        file_name = self.view.file_name()
        window = self.view.window()

        cursor_text = self.view.substr(sublime.Region(0, line.b))
        testcafe_cmd = 'testcafe ' + browser + ' '

        if cmd == 'previous' and self.previous_cmd is not None:
            testcafe_cmd = self.previous_cmd
        if cmd == 'all':
            testcafe_cmd = testcafe_cmd + file_name
        else:
            testcafe_cmd = testcafe_cmd + self.get_testcafe_cmd(cursor_text, file_name)

        self.previous_cmd = testcafe_cmd[:]
        self.text_queue_lock.acquire()
        try:
            self.text_queue.clear()
            self.text_queue_proc = None
        finally:
            self.text_queue_lock.release()

        if not hasattr(self, 'output_view'):
            self.output_view = window.get_output_panel('testcafe')

        self.clear_output_view()

        self.proc = None

        print('Running testcafe: ' + testcafe_cmd)

        show_panel_on_build = sublime.load_settings('Preferences.sublime-settings').get('show_panel_on_build', True)
        if show_panel_on_build:
            window.run_command('show_panel', {'panel': 'output.testcafe'})

        self.proc = AsyncProcess(testcafe_cmd, self)

        self.text_queue_lock.acquire()
        try:
            self.text_queue_proc = self.proc
        finally:
            self.text_queue_lock.release()

    def is_enabled(self, kill=False):
        if kill:
            return (self.proc is not None) and self.proc.poll()
        else:
            return True

    def append_string(self, proc, data):
        str = data.decode('utf-8')
        str = str.replace('\r\n', '\n').replace('\r', '\n')
        self.text_queue_lock.acquire()

        was_empty = False
        try:
            if proc != self.text_queue_proc:
                if proc:
                    proc.kill()
                return

            if len(self.text_queue) == 0:
                was_empty = True
                self.text_queue.append('')

            available = self.BLOCK_SIZE - len(self.text_queue[-1])

            if len(str) < available:
                cur = self.text_queue.pop()
                self.text_queue.append(cur + str)
            else:
                self.text_queue.append(str)

        finally:
            self.text_queue_lock.release()

        if was_empty:
            sublime.set_timeout(self.service_text_queue, 0)

    def service_text_queue(self):
        self.text_queue_lock.acquire()

        try:
            if len(self.text_queue) == 0:
                return

            str = self.text_queue.popleft()
            is_empty = (len(self.text_queue) == 0)
        finally:
            self.text_queue_lock.release()

        self.append_data_to_output_view(str)

        if not is_empty:
            sublime.set_timeout(self.service_text_queue, 1)
