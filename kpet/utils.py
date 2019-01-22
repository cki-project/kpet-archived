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
"""Utils used across kpet's commands"""
import os
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import tempfile
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from kpet.exceptions import ActionNotFound


def get_jinja_template(tree, dbdir):
    """
    Get a jinja template instance by tree
    Args:
        tree:   The kernel "tree" name
        dbdir:  Path to the kpet-db
    Returns:
        A jinja template instance
    """
    template_dirs = [os.path.join(dbdir, 'trees')]
    template_dirs.append(os.path.join(dbdir, 'layout'))
    jinja_env = Environment(
        loader=FileSystemLoader(template_dirs),
        autoescape=select_autoescape(
            enabled_extensions=('xml'),
            default_for_string=True,
        ),
    )
    template_file = "{}.xml".format(tree)
    template = jinja_env.get_template(template_file)
    return template


def patch2localfile(patches, workdir):
    """Convert all patches in local files"""
    result = []
    for patch in patches:
        # check if it's an url
        if urlparse(patch).scheme:
            response = requests.get(patch)
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
