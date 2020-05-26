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
"""Miscellaneous routines"""
from urllib.parse import urlparse
from textwrap import indent


class ActionNotFound(Exception):
    """Raised when an action is not found"""


def is_url(string):
    """Check if a string can be interpreted as a URL"""
    return bool(urlparse(string).scheme)


def format_exception_stack(exc):
    """
    Format an exception's context stack as a series of indented messages.

    Args:
        exc:    The exception to format the stack of.

    Returns:
        The formatted exception stack.
    """
    assert isinstance(exc, Exception)
    string = ""
    prefix = ""
    while True:
        string += indent(str(exc), prefix)
        if exc.__context__:
            string += ":\n"
            prefix += "  "
            exc = exc.__context__
        else:
            break
    return string


def get_repeated(iterable):
    """
    Get the set of repeated items from an iterable.

    Args:
        iterable:   The iterable to get repeated items from.

    Returns:
        The set of repeated items.
    """
    item_set = set()
    repeated_item_set = set()
    for item in iterable:
        (repeated_item_set if item in item_set else item_set).add(item)
    return repeated_item_set


def raise_action_not_found(action, command):
    """Raise the ActionNotFound exception"""
    raise ActionNotFound(
        'Action: "{}" not found in command "{}"'.format(
            action,
            command
        )
    )


def raise_invalid_database(database):
    """Raise an exception for a wrong database"""
    raise Exception(
        '"{}" is not a database directory.\nUse the --db option to specify '
        'an alternative database directory.'.format(
            database
        )
    )
