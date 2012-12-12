#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2012             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

table = None
mode = None
next_func = None

def begin(title, empty_text=None):
    global table, mode, next_func
    table = {
        "title": title,
        "headers" : [],
        "rows" : [],
    }
    if empty_text:
        table["empty_text"] = empty_text
    else:
        table["empty_text"] = _("No entries.")
    html.plug()
    mode = 'row'
    next_func = None

def finish_previous():
    if next_func:
        next_func(*next_args[0], **next_args[1])

def row(*posargs, **kwargs):
    finish_previous()
    global next_func, next_args
    next_func = add_row
    next_args = posargs, kwargs

def add_row():
    table["rows"].append([])

def cell(*posargs, **kwargs):
    finish_previous()
    global next_func, next_args
    next_func = add_cell
    next_args = posargs, kwargs

def add_cell(title, text="", css=None):
    htmlcode = text + html.drain()
    if len(table["rows"]) == 1: # first row -> pick headers
        table["headers"].append(title)
    table["rows"][-1].append((htmlcode, css))

def end():
    finish_previous()
    html.unplug()
    html.write("<h3>%s</h3>" % table["title"])
    if not table["rows"]:
        html.write("<div class=info>%s</div>" % table["empty_text"])
        return

    html.write("<table class=data>\n")
    html.write("  <tr>")
    for header in table["headers"]:
        html.write("    <th>%s</th>\n" % header)
    html.write("  </tr>\n")

    odd = "even"
    # TODO: Sorting
    for row in table["rows"]:
        # TODO: Filtering
        odd = odd == "odd" and "even" or "odd"
        html.write('  <tr class="data %s0">\n' % odd)
        for cell_content, css_classes in row:
            html.write("    <td%s>" % (css_classes and (" class='%s'" % css_classes) or ""))
            html.write(cell_content)
            html.write("</td>\n")
        html.write("</tr>\n")
    html.write("</table>\n")


