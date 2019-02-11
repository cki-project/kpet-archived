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
import re


class UnrecognizedPatchFormat(Exception):
    """Raised when can't extract any source file from a patch"""


class UnrecognizedPatchPathFormat(Exception):
    """Raised when can't extract source file path from a diff header"""


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


def get_test_cases(src_files, database):
    """
    Get test case names by querying database according to source files.
    Args:
        src_files: List of kernel source files
        database:  Database instance
    Returns:
        All names of test cases applicable to the src_files. It'll return all
        of them if src_files is empty.
    """
    testcases = set()

    for suite in database.testsuites.values():
        for pattern in suite.patterns:
            if not src_files:
                testcases.add(pattern['testcase_name'])
            else:
                for src_path in src_files:
                    if pattern['pattern'].match(src_path):
                        testcases.add(pattern['testcase_name'])

    return testcases


def get_property(property_name, test_names, database, required=False):
    """
    Get the property for every test name passed.
    Args:
        property_name: Property name e.g. hostRequires, tasks, partitions, etc
        test_names:    List of test names
        database:      Database instance
        required:      True if the property is mandatory, otherwise False
    Raises:
        KeyError:      When the property is not found and it is required.
    Returns:
        A set of the property values.
    """
    result = set()

    for testsuite in database.testsuites.values():
        for testcase in testsuite.cases:
            if testcase['name'] in test_names:
                try:
                    property_value = testcase[property_name]
                except KeyError:
                    if required:
                        raise
                    continue
                if property_value is not None:
                    result.add(property_value)
    return result
