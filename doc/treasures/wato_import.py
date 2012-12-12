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

#Author: Bastian Kuhn bk@mathias-kettner.de

import os
import sys

try:
    datei = open(sys.argv[1],'r') 
except IndexError:
    print """Place this file in your Wato directory
    Usage: ./wato_import.py csvfile.csv
    CSV Example:
    wato_foldername;hostname;host_alias;oneor|moreHostTags"""
    sys.exit()

folders = {}
for line in datei:
    ordner, name, alias, tag = line.split(';')
    if ordner:
        try:
            os.mkdir(ordner)
        except os.error:
            folder_exsits = True
        folders.setdefault(ordner,[])

        folders[ordner].append((name,alias,tag.strip()))
datei.close()


for folder in folders:
    all_hosts = "" 
    host_attributes = "" 
    for name, alias, tag in folders[folder]:
        all_hosts += "'%s|%s',\n" % (name, tag)
        host_attributes += "'%s' : {'alias' : u'%s' },\n" % (name, alias)

    ziel = open(folder + '/hosts.mk','w') 
    ziel.write('all_hosts += [')
    ziel.write(all_hosts)
    ziel.write(']\n\n')
    ziel.write('host_attributes.update({')
    ziel.write(host_attributes)
    ziel.write('})')
    ziel.close()
