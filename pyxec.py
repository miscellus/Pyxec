import sublime
import sublime_plugin
import io
import sys

context_setup_code = """\
import math
from math import *
from datetime import *
from time import *
from itertools import *
from random import *
from pprint import *
from collections import *
from urllib.request import urlopen
import io

def average(nums):
    return sum(nums) / len(nums)

avg = average

_sin = sin
def sin(x):
    return _sin(radians(x))

_cos = cos
def cos(x):
    return _cos(radians(x))

_tan = tan
def tan(x):
    return degrees(_tan(x))

_atan2 = atan2
def atan2(y, x):
    return degrees(_atan2(y, x))

def gcd(*args):
    it = iter(args)
    a = next(it)
    for b in it:
        while b > 0:
            a, b = b, a % b
    return a

def lcm(*args):
    it = iter(args)
    a = next(it)
    for b in it:
        c, d = a, b
        while d > 0:
            c, d = d, c % d
        a *= b // c
    return a

def modexp(base, exponent, modulus):
    if modulus == 1:
        return 0
    result = 1
    base %= modulus
    while exponent > 0:
        if exponent & 1 == 1:
            result = (result * base) % modulus
        exponent >>= 1
        base = (base * base) % modulus
    return result

def extended_euclid(phi, e):
    a = phi
    b = e
    c = phi
    d = 1

    while b != 1:
        t = a//b
        a, b = b, (a - b*t)
        c, d = d, (c - d*t) % phi

    return d

def rsa_encrypt(message, public_key, modulus):
    return modexp(message, public_key, modulus)

def rsa_decrypt(cypher, private_key, modulus):
    return modexp(cypher, private_key, modulus)

def urlget(url, enc='utf8'):
    return urlopen(url).read().decode(enc)
"""

context = {}
def init_context():
    global context
    context.clear()
    exec(context_setup_code, context)
init_context()

def bind_out_func(out_stream):
    def out(*args, end="\n", sep=" "):
        out_stream.write(sep.join(map(str, args)) + end)
    return out

def error(e):
    msg = "Pyxec: " + str(e)
    print(msg)
    sublime.status_message(msg)
    raise e

def exec_region(region, view, edit):
    s = view.substr(region)
    try:
        exec_out = io.StringIO()
        context["out"] = bind_out_func(exec_out)
        exec(s, context)
        out_text = exec_out.getvalue().rstrip()
        exec_out.close()
        return out_text
    except Exception as e:
        error(e)

def eval_region(region, view, edit):
    s = view.substr(region)
    try:
        return str(eval(s, context))
    except Exception as e:
        error(e)

class PyxecInitContextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        init_context()

def expand_empty_region_buffer(region, view):
    if region.empty():
        return sublime.Region(0, view.size()), True
    else:
        return region, False

def expand_empty_region_line(region, view):
    return view.line(region) if region.empty() else region

class PyxecExecReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        selections = view.sel()
        for region in selections:
            region, was_empty = expand_empty_region_buffer(region, view)
            out_text = exec_region(region, view, edit)
            self.view.replace(edit, region, out_text)
            if was_empty:
                break
        sublime.status_message("Pyxec: Execution completed.")

class PyxecExecToClipboardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        buffer_for_clipboard = []
        for region in view.sel():
            region, was_empty = expand_empty_region_buffer(region, view)
            out_text = exec_region(region, view, edit)
            buffer_for_clipboard.append(out_text)
            if was_empty:
                break
        if len(buffer_for_clipboard) > 0:
            sublime.set_clipboard("\n".join(buffer_for_clipboard))
        sublime.status_message("Pyxec: Execution completed.")

class PyxecEvalToClipboardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        buffer_for_clipboard = []
        for region in view.sel():
            region = expand_empty_region_line(region, view)
            out_text = eval_region(region, view, edit)
            buffer_for_clipboard.append(out_text)
        sublime.set_clipboard("\n".join(buffer_for_clipboard))
        sublime.status_message("Pyxec: Evaluation completed.")

class PyxecEvalReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for region in reversed(view.sel()):
            region = expand_empty_region_line(region, view)
            out_text = eval_region(region, view, edit)
            view.replace(edit, region, out_text)
        sublime.status_message("Pyxec: Evaluation completed.")