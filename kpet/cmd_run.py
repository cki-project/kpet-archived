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
import sys
import tempfile
import shutil
from kpet import misc, targeted, data, run


def get_src_files(patches, pw_cookie=None):
    """
    Get the set of files modified by a list of patches.

    Args:
        patches:   List of patches, they can be local files or remote urls
        pw_cookie: Session cookie to Patchwork instance if login is required,
                   None otherwise
    """
    tmpdir = tempfile.mkdtemp(suffix='kpet')
    try:
        patches = misc.patch2localfile(patches, tmpdir, pw_cookie)
        return targeted.get_src_files(patches)
    finally:
        shutil.rmtree(tmpdir)


def main(args):
    """Main function for the `run` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)
    if args.action == 'generate':
        if args.tree not in database.trees:
            raise Exception("Tree \"{}\" not found".format(args.tree))
        src_files = get_src_files(args.mboxes, args.pw_cookie)
        baserun = run.Base(database, src_files)
        content = baserun.generate(description=args.description,
                                   tree_name=args.tree,
                                   arch_name=args.arch,
                                   kernel_location=args.kernel,
                                   lint=not args.no_lint)
        if not args.output:
            sys.stdout.write(content)
        else:
            with open(args.output, 'w') as file_handler:
                file_handler.write(content)
    elif args.action == 'print-test-cases':
        src_files = get_src_files(args.patches, args.pw_cookie)
        case_name_list = sorted([case.name
                                 for case
                                 in database.match_case_list(src_files)])
        for case_name in case_name_list:
            print(case_name)
    else:
        misc.raise_action_not_found(args.action, args.command)
