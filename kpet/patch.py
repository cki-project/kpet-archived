# Copyright (c) 2019 Red Hat, Inc. All rights reserved. This copyrighted
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
"""Patch operations"""
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
    # pylint: disable=too-many-locals
    pattern = re.compile(r'^---$|'
                         r'^--- (\S+)(\s.*)?$\n'
                         r'^\+\+\+ (\S+)(\s.*)?$|'
                         r'^rename from (\S+)$\n'
                         r'^rename to (\S+)$',
                         re.MULTILINE)
    file_set = set()
    for patch_path in patch_path_list:
        # Some upstream patches are encoded as cp1252, iso-8859-1, or utf-8.
        # This is the recommended method from:
        #   http://python-notes.curiousefficiency.org/
        with open(patch_path, encoding="ascii",
                  errors="surrogateescape") as patch_file:
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
