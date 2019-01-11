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


class UnrecognizedPatchPathFormat(Exception):
    """Raised when can't extract source file path from a diff header"""


class TestCase(object):
    """ A class for testname and soaking data parsed."""
    # pylint: disable=useless-object-inheritance
    def __init__(self, testname, soak_data):
        self.testname = testname
        self.soak_data = soak_data

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.testname

    def __eq__(self, other):
        return self.testname == other.testname and \
               self.soak_data == other.soak_data

    def __hash__(self):
        return hash(self.testname)


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
    soaks = []
    for _, path in layout.items():
        pattern_file = os.path.join(dbdir, 'layout', path)

        with open(pattern_file) as file_handler:
            pattern_parsed = json.load(file_handler)

        addition = pattern_parsed['patterns']
        patterns.extend(addition)
        try:
            soaks.append(pattern_parsed['soaking'])
        except KeyError:
            soaks.extend([None] * len(addition))

    return patterns, soaks


def __get_src_file_path(diff_header_path):
    """
    Extract source file path from a path from a ---/+++ diff header.
    Return None if file doesn't exist before/after the change. Throw an
    exception if the path is invalid.
    Args:
        diff_header_path: The file path from the ---/+++ diff header.
    Returns:
        Source file path if the file exists before/after the change.
    Raises:
        UnrecognizedPatchPathFormat: the diff header file path was invalid.
    """
    if diff_header_path == "/dev/null":
        return None
    slash_idx = diff_header_path.find("/")
    # If path has no slash, starts with a slash, or ends with a slash
    if slash_idx <= 0 or diff_header_path[-1] == "/":
        raise UnrecognizedPatchPathFormat(diff_header_path)
    # Strip top directory
    return diff_header_path[slash_idx + 1:]


def get_src_files(patch_path_list):
    """
    Get paths to source files modified by patches in the specified files.
    Args:
        patch_path_list: List of patch file paths, they can't be URLs.
    Returns:
        A set of source file paths modified by the patches.
    Raises:
        UnrecognizedPatchFormat: a patch format was invalid.
        UnrecognizedPatchPathFormat: a path in a diff header was invalid.
    """
    pattern = re.compile(r'^---$|'
                         r'^--- (\S+)(\s.*)?$\n'
                         r'^\+\+\+ (\S+)(\s.*)?$|'
                         r'^rename from (\S+)$\n'
                         r'^rename to (\S+)$',
                         re.MULTILINE)
    file_set = set()
    for patch_path in patch_path_list:
        with open(patch_path) as patch_file:
            patch_content = patch_file.read()
            patch_file_set = set()
            for match in re.finditer(pattern, patch_content):
                if match.group(0) == "---":
                    patch_file_set = set()
                else:
                    (change_old, _, change_new, _, rename_old, rename_new) = \
                        match.groups()
                    if change_old and change_new:
                        old_file = __get_src_file_path(change_old)
                        new_file = __get_src_file_path(change_new)
                        if not old_file and not new_file:
                            raise UnrecognizedPatchFormat(patch_content)
                        if old_file:
                            patch_file_set.add(old_file)
                        if new_file:
                            patch_file_set.add(new_file)
                    else:
                        patch_file_set.add(rename_old)
                        patch_file_set.add(rename_new)
            if patch_file_set:
                file_set |= patch_file_set
            else:
                raise UnrecognizedPatchFormat(patch_content)
    return file_set


def get_layout(dbdir):
    """
    Load layout from a database.
    Args:
        dbdir: Path to the kpet-db
    Returns:
        Layout object loaded from the database.
    """
    path = os.path.join(dbdir, 'layout', 'layout.json')
    with open(path) as handle:
        obj = json.load(handle)
    assert obj['schema']['version'] == 1
    return obj['testsuites']


def get_test_cases(src_files, dbdir):
    """
    Get test cases by querying layout according to source files.
    Args:
        src_files: List of kernel source files
        dbdir:  Path to the kpet-db
    Returns: TestCase objects, all test cases applicable to the src_files.
        It'll return all of them if src_files is empty.
    """
    layout = get_layout(dbdir)
    patterns, soaks = get_patterns_by_layout(layout, dbdir)

    test_cases = set()
    for pattern_item, soak_item in zip(patterns, soaks):
        if not src_files:
            test_cases.add(TestCase(pattern_item['testcase_name'], soak_item))
        else:
            for src_path in src_files:
                if re.match(pattern_item['pattern'], src_path):
                    test_cases.add(TestCase(pattern_item['testcase_name'],
                                            soak_item))

    return test_cases


def get_all_test_cases(dbdir):
    """
    Get a generator iterating over all testcases defined in the database.
    Args:
        dbdir: Path to the kpet-db
    Returns:
        A generator iterating over all test cases.
    """
    for _, path in get_layout(dbdir).items():
        pattern_file = os.path.join(dbdir, 'layout', path)
        with open(pattern_file) as file_handler:
            pattern = json.load(file_handler)
        for testcase in pattern['cases']:
            yield testcase


def get_tasks(test_names, dbdir):
    """
    Get the corresponding "task" template path for every test name passed.
    Args:
        testcase: A list of TestCase objects with
        dbdir:      Path to the kpet-db
    Returns:
        A set of paths to "task" template files.
    """
    result = []
    processed = set()
    testcases_all = list(get_all_test_cases(dbdir))

    for test_name in test_names:
        for testcase in testcases_all:
            name = testcase['name']
            if test_name == name and name not in processed:
                processed.add(name)
                result.append(testcase['tasks'])

    return result


def get_host_requires(test_names, dbdir):
    """
    Get the corresponding "hostRequires" template path for every test name
    passed.
    Args:
        test_names: List of test names
        dbdir:      Path to the kpet-db
    Returns:
        A set of paths to "hostRequires" template files.
    """
    result = set()
    for testcase in get_all_test_cases(dbdir):
        if testcase['name'] in test_names:
            host_requires = testcase.get('hostRequires', None)
            if host_requires:
                result.add(host_requires)
    return result


def get_partitions(test_names, dbdir):
    """
    Get the corresponding "partitions" template path for every test name
    passed.
    Args:
        test_names: List of test names
        dbdir:      Path to the kpet-db
    Returns:
        A set of paths to "partitions" template files.
    """
    result = set()
    for testcase in get_all_test_cases(dbdir):
        if testcase['name'] in test_names:
            partitions = testcase.get('partitions', None)
            if partitions:
                result.add(partitions)
    return result
