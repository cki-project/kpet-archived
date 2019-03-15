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
"""The "run" command"""
import sys
import tempfile
import shutil
from kpet import misc, targeted, data, run, cmd_misc


def build(cmds_parser, common_parser):
    """Build the argument parser for the run command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        'run',
        help='Test suite run, default action "generate"',
    )
    generate_parser = action_subparser.add_parser(
        "generate",
        help='Generate the information required for a test run',
        parents=[common_parser],
    )
    generate_parser.add_argument(
        '-d',
        '--description',
        default='',
        help='An arbitrary text describing the run'
    )
    generate_parser.add_argument(
        '-o',
        '--output',
        default=None,
        help='Path where will be saved the xml, default is stdout'
    )
    generate_parser.add_argument(
        '--pw-cookie',
        default=None,
        help='Patchwork session cookie in case a login is required'
    )
    generate_parser.add_argument(
        '-t',
        '--tree',
        required=True,
        help='kernel "tree" name, chosen from "tree list" output, or "MAIL"'
    )
    generate_parser.add_argument(
        '-a',
        '--arch',
        default='x86_64',
        help='An architecture chosen from "arch list" output'
    )
    generate_parser.add_argument(
        '--type',
        default='auto',
        choices=['auto', 'tarball-url', 'rpm-url', 'tarball-path', 'rpm-path'],
        help='Type of the kernel reference'
    )
    generate_parser.add_argument(
        '-k',
        '--kernel',
        required=True,
        help='Compiled kernel'
    )
    generate_parser.add_argument(
        '-c',
        '--cover-letter',
        default='no cover letter',
        help='Patch series cover letter mbox URL/path'
    )
    generate_parser.add_argument(
        '--no-lint',
        action='store_true',
        help='Do not lint and reformat output XML'
    )
    generate_parser.add_argument(
        'mboxes',
        nargs='*',
        default=[],
        help='List of mbox URLs/paths comprising the patch series'
    )
    print_test_cases_parser = action_subparser.add_parser(
        "print-test-cases",
        help="Print test cases applicable to the patches",
        parents=[common_parser],
    )
    print_test_cases_parser.add_argument(
        'patches',
        nargs='*',
        default=[],
        help='List of patches URLs/paths'
    )
    print_test_cases_parser.add_argument(
        '--pw-cookie',
        default=None,
        help='Patchwork session cookie in case a login is required'
    )


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
        if args.arch not in database.arches:
            raise Exception("Architecture \"{}\" not found".format(args.arch))
        if args.tree not in database.trees:
            raise Exception("Tree \"{}\" not found".format(args.tree))
        src_files = get_src_files(args.mboxes, args.pw_cookie)
        target = data.Target(trees=args.tree,
                             arches=args.arch,
                             sources=src_files)
        baserun = run.Base(database, target)
        content = baserun.generate(description=args.description,
                                   kernel_location=args.kernel,
                                   lint=not args.no_lint)
        if not args.output:
            sys.stdout.write(content)
        else:
            with open(args.output, 'w') as file_handler:
                file_handler.write(content)
    elif args.action == 'print-test-cases':
        src_files = get_src_files(args.patches, args.pw_cookie)
        target = data.Target(sources=src_files)
        baserun = run.Base(database, target)
        case_name_list = []
        for host in baserun.hosts:
            for suite in host.suites:
                for case in suite.cases:
                    case_name_list.append(case.name)
        for case_name in sorted(case_name_list):
            print(case_name)
    else:
        misc.raise_action_not_found(args.action, args.command)
