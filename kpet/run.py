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
"""Module where the `run` command is implemented"""
from __future__ import print_function
import tempfile
import shutil
import os
from kpet import utils, targeted, data


def get_test_cases(patches, database, pw_cookie=None):
    """
    Return test cases by querying layout according list of patch files.
    Args:
        patches:   List of patches, they can be local files or remote urls
        database:  Database instance
        pw_cookie: Session cookie to Patchwork instance if login is required,
                   None otherwise
    """
    tmpdir = tempfile.mkdtemp(suffix='kpet')
    try:
        patches = utils.patch2localfile(patches, tmpdir, pw_cookie)
        src_files = targeted.get_src_files(patches)
        return sorted(targeted.get_test_cases(src_files, database.dir_path))
    finally:
        shutil.rmtree(tmpdir)


def print_test_cases(patches, database, pw_cookie=None):
    """
    Print test cases by querying layout according list of patch files.
    Args:
        patches:   List of patches, they can be local files or remote urls
        database:  Database instance
        pw_cookie: Session cookie to Patchwork instance if login is required,
                   None otherwise
    """
    for test_case in get_test_cases(patches, database, pw_cookie):
        print(test_case)


# pylint: disable=too-many-arguments
def generate(template, template_params, patches, database, output,
             pw_cookie=None):
    """
    Generate an xml output compatible with beaker.
    Args:
        template:        Jinja template instance
        template_params: A dictionary with template parameters such as arch,
                         whiteboard description, etc.
        patches:         List of patches, can be local files or remote urls
        database:        Database instance
        output:          Output file where beaker xml will be rendered
        pw_cookie:       Session cookie to Patchwork instance if login is
                         required, None otherwise
    """
    test_names = get_test_cases(patches, database, pw_cookie)
    template_params['TEST_CASES'] = sorted(
        targeted.get_property('tasks', test_names, database.dir_path,
                              required=True)
    )
    template_params['TEST_CASES_HOST_REQUIRES'] = sorted(
        targeted.get_property('hostRequires', test_names, database.dir_path)
    )
    template_params['TEST_CASES_PARTITIONS'] = sorted(
        targeted.get_property('partitions', test_names, database.dir_path)
    )
    template_params['TEST_CASES_KICKSTART'] = sorted(
        targeted.get_property('kickstart', test_names, database.dir_path)
    )
    content = template.render(template_params)
    if not output:
        print(content)
    else:
        with open(output, 'w') as file_handler:
            file_handler.write(content)


def main(args):
    """Main function for the `run` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)
    if args.action == 'generate':
        template = utils.get_jinja_template(args.tree, args.db)
        template_params = {
            'DESCRIPTION': args.description,
            'ARCH': args.arch,
            'KURL': args.kernel,
            'TREE': args.tree,
            'getenv': os.getenv,
        }
        generate(template, template_params, args.mboxes, database,
                 args.output, args.pw_cookie)
    elif args.action == 'print-test-cases':
        print_test_cases(args.patches, database, args.pw_cookie)
    else:
        utils.raise_action_not_found(args.action, args.command)
