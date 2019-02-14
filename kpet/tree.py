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
"""Module where the `tree` command is implemented"""
import os
import errno
from kpet import utils


class TemplateDirNotFound(Exception):
    """Raised when template dir is not found under the dbdir"""


def list_tree(db_path):
    """
    List all the trees a.k.a templates available sorted on the current db.

    Args:
        db_path: path to kpet-db
    """
    template_dir = os.path.join(db_path, 'templates')
    try:
        files = sorted(os.listdir(template_dir))
    except OSError as error:
        if error.errno == errno.ENOENT:
            raise TemplateDirNotFound(
                'Missing `templates` folder on {}'.format(db_path)
            )
        else:
            raise
    for filename in files:
        if not filename.endswith('.xml'):
            continue
        tree, _ = os.path.splitext(filename)
        print(tree)


def main(args):
    """Main function for the `tree` command"""
    if args.action == 'list':
        list_tree(args.db)
    else:
        utils.raise_action_not_found(args.action, args.command)
