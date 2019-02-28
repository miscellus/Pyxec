import sublime
import sublime_plugin
from io import StringIO

# Globals
context = {}
context_setup_code = """\
PYXEC_VERSION = "1.0"

import math
from math import *
from itertools import *
from random import *
from pprint import *
from collections import *
"""

def init_context():
    global context
    context.clear()
    exec(context_setup_code, context)
init_context()

def pyxec_error(e):
    msg = "Pyxec: " + str(e)
    print(msg)
    sublime.status_message(msg)
    raise e


class PyxecInitContextCommand(sublime_plugin.Command):
    def run(self, edit):
        init_context()

class PyxecExecuteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global context

        view = self.view
        view_size = view.size()
        regions = view.sel()
        result_strings = []

        for region in regions:
            if region.empty():
                region = sublime.Region(0, view_size)

            region_string = view.substr(region)

            try:
                with StringIO() as exec_out_stream:

                    def print_func(*args, end="\n", sep=" "):
                        exec_out_stream.write(sep.join(map(str, args)) + end)

                    context["print"] = print_func
                    exec(region_string, context)
                    result_string = exec_out_stream.getvalue().rstrip()

                    result_strings.append(result_string)

            except Exception as e:
                pyxec_error(e)

        joined_result_strings = "\n".join(result_strings)

        # Get Pyxec View
        pyxec_view_name = "Pyxec View"
        window = sublime.active_window()
        original_view = window.active_view()

        try:
            pyxec_view = self.pyxec_sheet.view()
            pyxec_view.name()

        except:
            pyxec_view = None
            for candidate_view in window.views():
                if candidate_view.name() == pyxec_view_name:
                    pyxec_view = candidate_view
                    break
            else: # no break
                pyxec_view = window.new_file()
                pyxec_view.set_name(pyxec_view_name)

            (group, view_index) = window.get_view_index(pyxec_view)
            self.pyxec_sheet = window.sheets_in_group(group)[view_index]

        window.focus_view(pyxec_view)
        pyxec_view.erase(edit, sublime.Region(0, pyxec_view.size()))
        pyxec_view.insert(edit, pyxec_view.size(), joined_result_strings)
        window.focus_view(view)

        sublime.status_message("Pyxec: Execution completed.")

class PyxecEvaluateReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global context

        view = self.view
        regions = view.sel()
        result_strings = []

        for region in regions:
            if region.empty():
                region = view.line(region)

            region_string = view.substr(region)

            try:
                result_string = str(eval(region_string, context))
                result_strings.append(result_string)
                view.replace(edit, region, result_string)

                if region.size() >= view.size():
                    break

            except Exception as e:
                pyxec_error(e)

        joined_result_strings = "\n".join(result_strings)
        sublime.set_clipboard(joined_result_strings)

        sublime.status_message("Pyxec: Evaluation completed.")
