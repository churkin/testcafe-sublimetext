import sublime_plugin
import os
import subprocess
import json
import copy

PACKAGE_PATH = os.path.dirname(__file__)
CONTEXT_MENU_FILE_NAME = 'Context.sublime-menu'
SIDE_BAR_FILE_NAME = 'Side Bar.sublime-menu'
COMMANDS_FILE_NAME = 'TestCafe.sublime-commands'
KEYMAP_FILE_NAME = 'Default.sublime-keymap'

TEMPLATES = {
    'context_menu': [{'caption': 'TestCafe', 'id': 'testcafe', 'children': [{
        'args': {'cmd': 'previous'},
        'caption': 'Rerun previous tests',
        'command': 'test_cafe'
    }, {'caption': '-'}]}],
    'side_bar_menu': [{'caption': 'TestCafe', 'children': [{
        'args': {'cmd': 'previous'},
        'caption': 'Rerun previous tests',
        'command': 'test_cafe',
        'mnemonic': 'p'
    }, {'caption': '-'}]}],
    'keymap': [{'args': {'cmd': 'previous'}, 'command': 'test_cafe',
                'keys': ['ctrl+alt+p']}, {'args': {'panel': 'output.testcafe'},
                                          'command': 'show_panel', 'keys': ['ctrl+alt+l']}],
    'commands': [{'args': {'panel': 'output.testcafe'}, 'caption': 'TestCafe: Show output panel',
                  "command": "show_panel"}, {"args": {"cmd": "previous"}, "caption": "TestCafe: Rerun previous tests",
                                             "command": "test_cafe"}]
}


def write_to_file(file_name, content):
    f = open(PACKAGE_PATH + '\\' + file_name, 'w')
    f.write(json.dumps(content, sort_keys=True, indent=4, separators=(',', ': ')))
    f.close()


def update_browsers():
    browser_list = subprocess.getoutput('testcafe --list-browsers').split('\n')
    templates = copy.deepcopy(TEMPLATES)

    for browser in browser_list:
        browserIndex = browser_list.index(browser) + 1

        command = {'command': 'test_cafe',
                   'caption': 'TestCafe: Run in {0}'.format(browser),
                   'args': {'browser': browser}}
        templates['commands'].append(command)
        comtext_menu_item = {'command': 'test_cafe',
                             'caption': 'Run in {0}'.format(browser, browserIndex),
                             'args': {'browser': browser}}
        templates['context_menu'][0]['children'].append(comtext_menu_item)
        side_bar_menu_item = {'command': 'test_cafe',
                              'caption': 'Run in {0}'.format(browser, browserIndex),
                              'args': {'browser': browser, 'cmd': 'all'}}
        templates['side_bar_menu'][0]['children'].append(side_bar_menu_item)
        keymap_item = {'command': 'test_cafe', 'keys': ["ctrl+alt+{0}".format(browserIndex)],
                       'args': {'browser': browser}}
        templates['keymap'].append(keymap_item)

    write_to_file(KEYMAP_FILE_NAME, templates['keymap'])
    write_to_file(COMMANDS_FILE_NAME, templates['commands'])
    write_to_file(CONTEXT_MENU_FILE_NAME, templates['context_menu'])
    write_to_file(SIDE_BAR_FILE_NAME, templates['side_bar_menu'])


class TestCafeBrowsersCommand(sublime_plugin.WindowCommand):
    def run(self):
        update_browsers()


if not os.path.isfile(PACKAGE_PATH + '\\' + COMMANDS_FILE_NAME):
    update_browsers()
