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


def attr_parentage(obj, attr, omit_none=True):
    """
    Ascend object parentage, yielding values of the specified attribute for
    each. Omit None values by default.

    Args:
        obj:        The object to start ascending at, or None for no object.
                    Must have "parent" attribute with either the parent object
                    or None, as must all the parent objects thus linked.
        attr:       The name of the attribute to return values of.
        omit_none:  True, if None attribute values should be omitted.
                    False, if all attribute values should yielded.

    Yields:
        Values of the specified attribute in order of parentage.
    """
    assert obj is None or hasattr(obj, "parent")
    assert isinstance(attr, str)
    while obj is not None:
        value = getattr(obj, attr)
        if not omit_none or value is not None:
            yield value
        obj = obj.parent


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
