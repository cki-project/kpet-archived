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
import http.cookiejar as cookiejar
from urllib.parse import urlparse
import tempfile
import requests
from kpet.exceptions import ActionNotFound


def patch2localfile(patches, workdir, session_cookie=None):
    """Convert all patches in local files"""
    result = []
    for patch in patches:
        # check if it's an url
        if urlparse(patch).scheme:
            # Create a Patchwork session cookie if specified
            cookie_jar = None
            if session_cookie:
                domain = patch.rsplit('patch', 1)[0].strip('/').split('/')[-1]
                cookie = cookiejar.Cookie(0, 'sessionid', session_cookie, None,
                                          False, domain, False, False, '/',
                                          False, False, None, False, None,
                                          None, {})
                cookie_jar = cookiejar.CookieJar()
                cookie_jar.set_cookie(cookie)

            response = requests.get(patch, cookies=cookie_jar)
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
