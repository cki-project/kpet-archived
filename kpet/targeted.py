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
"""Targeted testing - matching patches to applicable test cases"""
import os
import json
import re


class UnrecognizedPatchFormat(Exception):
    """Raised when can't extract any source file from a patch"""


def get_patterns_by_layout(layout, dbdir):
    """
    Return patterns of layout.
    Args:
        layout: The content of the layout.json file of the corresponding db
        dbdir:  Path to the kpet-db
    Returns:
        List of tuple (regex, testcase-name)
    """
    patterns = []
    for _, path in layout.items():
        pattern_file = os.path.join(dbdir, 'layout', path)
        with open(pattern_file) as file_handler:
            pattern_parsed = json.load(file_handler)
        patterns.extend(pattern_parsed['patterns'])
    return patterns


def get_src_files(patches):
    """
    Get source files from the list of patch files.
    Args:
        patches: List of patches, they can be local files or remote urls
    """
    pattern = re.compile(r'diff --git a/(.*) b/(.*)')
    src_files = set()
    for patch_path in patches:
        with open(patch_path) as patch_handler:
            patch_content = patch_handler.read()
            match = re.findall(pattern, patch_content)
            if not match:
                raise UnrecognizedPatchFormat(patch_content)
            for src_match in match:
                src_files.update(src_match)
    return src_files


def get_layout(dbdir):
    """
    Load layout from a database.
    Args:
        dbdir: Path to the kpet-db
    Returns:
        Layout object loaded from the database.
    """
    layout_path = os.path.join(dbdir, 'layout', 'layout.json')
    with open(layout_path) as layout_handler:
        layout = json.load(layout_handler)
    return layout


def get_test_cases(src_files, dbdir):
    """
    Get test cases by querying layout according to source files.
    Args:
        src_files: List of kernel source files
        dbdir:  Path to the kpet-db
    Returns:
        All test cases applicable to the src_files. It'll return all of them
        if src_files is empty.
    """
    layout = get_layout(dbdir)
    patterns = get_patterns_by_layout(layout, dbdir)

    test_cases = set()
    for pattern_item in patterns:
        if not src_files:
            test_cases.add(pattern_item['case'])
        else:
            for src_path in src_files:
                if re.match(pattern_item['pattern'], src_path):
                    test_cases.add(pattern_item['case'])
    return test_cases
