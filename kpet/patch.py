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
from urllib.parse import urlparse
import requests


class UnrecognizedFormat(Exception):
    """Unrecognized patch format"""


class UnrecognizedPathFormat(UnrecognizedFormat):
    """Unrecognized format of a path in a diff header of a patch"""


def _get_src_from_diff_header_path(diff_header_path):
    """
    Extract source file path from a path from a ---/+++ diff header.
    Return None if file doesn't exist before/after the change. Throw an
    exception if the path is invalid.
    Args:
        diff_header_path: The file path from the ---/+++ diff header.
    Returns:
        Source file path if the file exists before/after the change.
    Raises:
        UnrecognizedPathFormat: the diff header file path was invalid.
    """
    if diff_header_path == "/dev/null":
        return None
    slash_idx = diff_header_path.find("/")
    # If path has no slash, starts with a slash, or ends with a slash
    if slash_idx <= 0 or diff_header_path[-1] == "/":
        raise UnrecognizedPathFormat(diff_header_path)
    # Strip top directory
    return diff_header_path[slash_idx + 1:]


def get_src_set(patch):
    """
    Get the set of paths to source files modified by the patch.
    Args:
        patch: Contents of the patch to extract modified paths from.
    Returns:
        The set of source file paths modified by the patch.
    Raises:
        UnrecognizedFormat: patch format was invalid.
    """
    pattern = re.compile(r'^---$|'
                         r'^--- (\S+)(\s.*)?$\n'
                         r'^\+\+\+ (\S+)(\s.*)?$|'
                         r'^rename from (\S+)$\n'
                         r'^rename to (\S+)$',
                         re.MULTILINE)
    src_set = set()
    for match in re.finditer(pattern, patch):
        if match.group(0) == "---":
            src_set = set()
        else:
            (change_old, _, change_new, _, rename_old, rename_new) = \
                match.groups()
            if change_old and change_new:
                try:
                    old_file = _get_src_from_diff_header_path(change_old)
                    new_file = _get_src_from_diff_header_path(change_new)
                except UnrecognizedPathFormat:
                    raise UnrecognizedFormat("Invalid path in a diff header")
                if not old_file and not new_file:
                    raise UnrecognizedFormat("No valid paths in a diff header")
                if old_file:
                    src_set.add(old_file)
                if new_file:
                    src_set.add(new_file)
            else:
                src_set.add(rename_old)
                src_set.add(rename_new)
    if not src_set:
        raise UnrecognizedFormat("No changed files")
    return src_set


def load_from_location(location, cookies=None):
    """
    Load patch content from a patch location (URL or path).

    Args:
        location:   A patch location (URL or path).
        cookies:    A cookie jar object to use when fetching URL locations,
                    if not None.
    Returns:
        The patch content.
    """
    # If it's a url
    if urlparse(location).scheme:
        response = requests.get(location, cookies=cookies)
        response.raise_for_status()
        content = response.content
    # Else it's a local file
    else:
        # Some upstream patches are encoded as cp1252, iso-8859-1, or utf-8.
        # This is the recommended method from:
        #   http://python-notes.curiousefficiency.org/
        with open(location, encoding="ascii",
                  errors="surrogateescape") as patch_file:
            content = patch_file.read()
    return content


def get_src_set_from_location_set(location_set, cookies=None):
    """
    Get the set of paths to source files modified by patches at a set of
    locations.

    Args:
        location_set:   A set of locations (URLs or paths), to load patches
                        and extract the modified source files from. Can be any
                        iterable beside the set.
        cookies:        A cookie jar object to use when fetching URL
                        locations, if not None.
    Returns:
        The set of paths to modified source files.
    Raises:
        UnrecognizedFormat: The format of a patch was invalid.
    """
    src_set = set()
    for location in location_set:
        try:
            src_set |= get_src_set(load_from_location(location, cookies))
        except UnrecognizedFormat:
            raise UnrecognizedFormat("Can't parse contents of {}".
                                     format(location))
    return src_set
