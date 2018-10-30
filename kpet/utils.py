# Copyright (c) 2018 Red Hat, Inc. All rights reserved. This copyrighted
# material is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General Public
# License v.2 or later.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""Utils used across kpet's commands"""
import os
import json
import collections
import re
import logging


class TemplateNotFound(Exception):
    """Raised when an template is not found"""


def get_template_path(tree, dbdir):
    """Return the full path for the corresponding template"""
    filename = '{}.xml'.format(tree)
    path = os.path.join(dbdir, 'templates', filename)
    if not os.path.exists(path):
        raise TemplateNotFound(path)
    return path


def get_template_content(tree, dbdir):
    """Return the content for the corresponding template"""
    template_path = get_template_path(tree, dbdir)
    with open(template_path) as file_handler:
        return file_handler.read()


def smart_get_patterns_bylayout(d_layout, f_layout):
    """Return patterns of layout"""
    layout_prefix = os.path.dirname(os.path.realpath(f_layout))

    l_patterns = []
    for key in d_layout:
        val = d_layout[key]
        if val is None:
            continue

        s_file = os.path.join(layout_prefix, val)
        d_pattern = None
        with open(s_file, 'r') as file_handler:
            d_pattern = json.load(file_handler,
                                  object_pairs_hook=collections.OrderedDict)
        for pattern in d_pattern['patterns']:
            if pattern not in l_patterns:
                l_patterns.append(pattern)

    return l_patterns


def smart_get_src_files(l_patch):
    """Get source files according to list of patch files"""
    # USE `unidiff` instead (fixme)

    pattern = re.compile(r'^diff --git a/.* b/.*')

    l_src = []
    for f_patch in l_patch:
        with open(f_patch, 'r') as file_handler:
            while True:
                line = file_handler.readline()
                if not line:
                    break

                if pattern.match(line.strip()) is None:
                    continue

                line = line.rstrip()
                l_line = line.split(' ')
                srcfile = l_line[-1].replace('b/', '')
                if srcfile not in l_src:
                    l_src.append(srcfile)

    return l_src


def smart_get_test_cases(l_src, f_layout):
    """Get test cases by querying layout according to source files"""
    # get layout
    d_layout = None
    with open(f_layout, 'r') as file_handler:
        d_layout = json.load(file_handler,
                             object_pairs_hook=collections.OrderedDict)
        if d_layout is None:
            logging.error("Fail to get layout")
            return None

    # get patterns by layout
    l_patterns = smart_get_patterns_bylayout(d_layout, f_layout)
    if l_patterns is None:
        logging.error("Fail to get patterns")
        return None

    # get cases by patterns
    l_cases = []
    for element in l_patterns:
        pattern = element['pattern']
        case = element['case']

        pattern = re.compile(r'%s' % pattern)
        for f_src in l_src:
            ret = pattern.match(f_src)
            if ret is None:
                continue

            if case in l_cases:
                continue
            else:
                l_cases.append(case)

    return l_cases
