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
import tempfile
import requests


class ActionNotFound(Exception):
    """Raised when an action is not found"""


def is_url(string):
    """Check if a string can be interpreted as a URL"""
    return bool(urlparse(string).scheme)


def patch2localfile(patches, workdir, cookies=None):
    """
    Convert all patches to local files.

    Args:
        patches:    A list of patch paths or URLs.
        workdir:    Directory to place downloaded patches in.
        cookies:    A jar of cookies to send when downloading patches.
                    Optional.

    Returns:
        A list of patch paths.
    """
    result = []
    for patch in patches:
        if is_url(patch):
            response = requests.get(patch, cookies=cookies)
            response.raise_for_status()
            tmpfile = tempfile.mktemp(dir=workdir)
            with open(tmpfile, 'wb') as file_handler:
                file_handler.write(response.content)
            result.append(tmpfile)
        else:
            # it's a local file
            result.append(patch)
    return result


def raise_action_not_found(action, command):
    """Raise the ActionNotFound exception"""
    raise ActionNotFound(
        'Action: "{}" not found in command "{}"'.format(
            action,
            command
        )
    )
