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


class TemplateNotFound(Exception):
    """Raised when an template is not found"""


def get_template_path(tree, dbdir):
    """Return the full path for the corresponding template"""
    filename = '{}.xml'.format(tree)
    path = os.path.join(dbdir, 'templates', filename)
    if not os.path.exists(path):
        raise TemplateNotFound(path)
    return path


def get_template_content(tree, dbdir):
    """Return the content for the corresponding template"""
    template_path = get_template_path(tree, dbdir)
    with open(template_path) as file_handler:
        return file_handler.read()
