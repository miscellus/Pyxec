import sublime
import sublime_plugin

context_setup_code = """\
import math
from math import *
from itertools import *
from random import *
from pprint import *
from collections import *
"""

def pyxec_error(e):
    msg = "Pyxec: " + str(e)
    print(msg)
    sublime.status_message(msg)
    raise e

context = {}
def init_context():
    global context
    context.clear()
    exec(context_setup_code, context)
init_context()


class PyxecInitContextCommand(sublime_plugin.Command):
    def run(self, edit):
        init_context()

class PyxecExecuteCommand(sublime_plugin.TextCommand):

    pyxec_sheet = None

    def get_pyxec_view(self):
        pyxec_view_name = "Pyxec View"

        window = sublime.active_window()
        original_view = window.active_view()

        try:
            pyxec_view = pyxec_sheet.view()
            pyxec_view.name()

        except:
            pyxec_view = None
            for iv in window.views():
                if iv.name() == pyxec_view_name:
                    pyxec_view = iv
                    break
            if pyxec_view is None:
                pyxec_view = window.new_file()
                pyxec_view.set_name(pyxec_view_name)
            group, index = window.get_view_index(pyxec_view)
            pyxec_sheet = window.sheets_in_group(group)[index]

        window.focus_view(pyxec_view)
        window.focus_view(original_view)
        return pyxec_view

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
                with io.StringIO() as exec_out_stream:

                    def print_func(*args, end="\n", sep=" "):
                        exec_out_stream.write(sep.join(map(str, args)) + end)

                    context["print"] = print_func
                    exec(region_string, context)
                    result_string = exec_out_stream.getvalue().rstrip()

                    result_strings.append(result_string)

            except Exception as e:
                pyxec_error(e)

        joined_result_strings = "\n".join(result_strings)

        pyxec_view = get_pyxec_view()
        pyxec_view.erase(edit, sublime.Region(0, pyxec_view.size()))
        pyxec_view.insert(edit, pyxec_view.size(), joined_result_strings)
        sublime.active_window().focus_view(view)
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
