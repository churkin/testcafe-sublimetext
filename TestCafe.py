import sublime
import time
import threading
import sublime_plugin
import subprocess
import re
import sys
from subprocess import PIPE, Popen
from threading  import Thread

class TestCafeCommand(sublime_plugin.TextCommand):
  def show_tests_panel(self):
    if not hasattr(self, 'output_view'):
      hasattr(self, 'output_view')

    self.output_view = self.view.window().get_output_panel('testcafe_tests')
    self.clear_test_view()
    self.view.window().run_command('show_panel', {'panel': 'output.testcafe_tests'})

  def clear_test_view(self):
    self.output_view.set_read_only(False)
    edit = self.edit
    self.output_view.erase(edit, sublime.Region(0, self.output_view.size()))
    self.output_view.set_read_only(True)
  
  def append_data(self, data):
    self.output_view.set_read_only(False)
    edit = self.edit
    self.output_view.insert(edit, self.output_view.size(), data)
    self.output_view.set_read_only(True)
  
  def run(self, edit, **args):
    self.edit = edit
    selection = self.view.sel()[0]
    line = self.view.line(selection.b)
    line_text = self.view.substr(line)
    testcafe_command = 'testcafe chrome '

    if 'all_tests' in args:
      testcafe_command = testcafe_command + self.view.file_name()
    elif line_text.find('fixture') != -1:
      fixture = re.search("fixture(\s)+`(.*)`", line_text).group(1)	  
      testcafe_command = testcafe_command + self.view.file_name() + ' -f ' + '"' + fixture + '"'
    elif line_text.find('test') != -1:
      test = re.search("test\('(.*)'", line_text).group(1)  
      testcafe_command = testcafe_command + self.view.file_name() + ' -t ' + '"' + test + '"'

    #self.show_tests_panel()
    print('Running testcafe: ' + testcafe_command) 
    
    def readFromConsole(cmd, output_view, edit):
      proc = subprocess.Popen(cmd + ' && echo stop-sublime', shell=True, stdout=subprocess.PIPE)
      while True:
        line = proc.stdout.readline()
        line = str(line, 'utf-8')
        if not re.search('stop-sublime', line): 
          #output_view.set_read_only(False)
          #output_view.insert(edit, output_view.size(), line.rstrip())
          #output_view.set_read_only(True)
          print(line.rstrip())
        else:
          break

    readingThread = threading.Thread(target=readFromConsole, args=([testcafe_command, self.output_view, self.edit]))
    readingThread.daemon = True
    readingThread.start();

