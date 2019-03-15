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
"""Kernel location handling"""

import re
from kpet import misc


# The set of possible location types
TYPE_SET = {"tarball-url", "rpm-url", "repo-url",
            "tarball-path", "rpm-path", "repo-path"}


def type_detect(loc):
    """
    Detect kernel location type.

    Args:
        loc:    A kernel location string.

    Returns:
        Location type string (a member of "TYPE_SET"),
        or None if the type is unknown.
    """
    type_parts = []

    if re.match(r'.*\.tar\.gz$', loc):
        type_parts.append("tarball")
    elif re.match(r'.*\.rpm$', loc):
        type_parts.append("rpm")
    else:
        type_parts.append("repo")

    if misc.is_url(loc):
        type_parts.append("url")
    else:
        type_parts.append("path")

    type_str = "-".join(type_parts)
    assert type_str in TYPE_SET
    return type_str


def type_is_valid(type_str):
    """
    Check if a kernel location type is valid.

    Args:
        type_str:   Location type string to check.

    Returns:
        True if the location type is valid, False otherwise.
    """
    return type_str in TYPE_SET
