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
import http.cookiejar as cookiejar
import re
import sys
import tempfile
import shutil
from kpet import misc, targeted, data, run, cmd_misc, loc


def build_target(parser):
    """
    Add target-specifying arguments to a "run" sub-command parser.

    Args:
        parser: The parser to add arguments to.
    """
    parser.add_argument(
        '--pw-cookie',
        default=None,
        help='Patchwork session cookie in case a login is required'
    )
    parser.add_argument(
        '--cookies',
        metavar='FILE',
        default=None,
        help='Cookies to send when downloading patches, Netscape-format file.'
    )
    parser.add_argument(
        '-t',
        '--tree',
        required=True,
        help='Name of the specified kernel\'s tree. Required. ' +
        'See "kpet tree list" for recognized trees.'
    )
    parser.add_argument(
        '-a',
        '--arch',
        default='x86_64',
        help='Architecture of the specified kernel. Required. ' +
        'See "kpet arch list" for supported architectures.'
    )
    parser.add_argument(
        '-c',
        '--components',
        metavar='REGEX',
        help='A regular expression matching extra components included ' +
        'into the kernel build. ' +
        'See "kpet component list" for recognized components.'
    )
    parser.add_argument(
        '-s',
        '--sets',
        metavar='REGEX',
        help='A regular expression matching the sets of tests ' +
        'to restrict the run to. See "kpet set list" for available sets.'
    )
    parser.add_argument(
        '--type',
        default='auto',
        choices=['auto'] + sorted(loc.TYPE_SET),
        help='Type of the kernel location. Default "auto".'
    )
    parser.add_argument(
        '-k',
        '--kernel',
        required=True,
        help='Kernel location. Must be accessible by Beaker. Required.'
    )
    parser.add_argument(
        'mboxes',
        nargs='*',
        default=[],
        help='List of mbox URLs/paths comprising the patch series'
    )


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
        '--no-lint',
        action='store_true',
        help='Do not lint and reformat output XML'
    )
    build_target(generate_parser)

    print_test_cases_parser = action_subparser.add_parser(
        "print-test-cases",
        help="Print test cases applicable to the patches",
        parents=[common_parser],
    )
    build_target(print_test_cases_parser)


def get_src_files(patches, cookies=None):
    """
    Get the set of files modified by a list of patches.

    Args:
        patches:   List of patches, they can be local files or remote urls
        cookies:   A jar of cookies to send when downloading patches.
                   Optional.

    Returns:
        A set of source file paths modified by the patches.
    """
    tmpdir = tempfile.mkdtemp(suffix='kpet')
    try:
        patches = misc.patch2localfile(patches, tmpdir, cookies)
        return targeted.get_src_files(patches)
    finally:
        shutil.rmtree(tmpdir)


# pylint: disable=too-many-branches
def main_create_baserun(args, database):
    """
    Generate test execution data for specified test database and command-line
    arguments.

    Args:
        args:       Parsed command-line arguments.
        database:   The database to get test data from.

    Returns:
        Test execution data.
    """
    cookies = cookiejar.MozillaCookieJar()
    if args.cookies:
        cookies.load(args.cookies)
    if args.pw_cookie:
        for mbox in args.mboxes:
            if not misc.is_url(mbox):
                continue
            domain = mbox.rsplit('patch', 1)[0].strip('/').split('/')[-1]
            cookie = cookiejar.Cookie(0, 'sessionid', args.pw_cookie,
                                      None, False, domain, False, False,
                                      '/', False, False, None, False,
                                      None, None, {})
            cookies.set_cookie(cookie)
    src_files = get_src_files(args.mboxes, cookies)
    if args.arch not in database.arches:
        raise Exception("Architecture \"{}\" not found".format(args.arch))
    if args.tree not in database.trees:
        raise Exception("Tree \"{}\" not found".format(args.tree))
    if args.components is None:
        components = set()
    else:
        components = set(x for x in database.components
                         if re.fullmatch(args.components, x))
    if args.sets is None:
        sets = set()
    else:
        sets = set(x for x in database.sets if re.fullmatch(args.sets, x))
        if not sets:
            raise Exception("No test sets matched specified regular " +
                            "expression: {}".format(args.sets))
    if args.type == "auto":
        loc_type = loc.type_detect(args.kernel)
        if loc_type is None:
            raise \
                Exception(
                    "Cannot determine the type of kernel location \"{}\". "
                    "Expecting a path to/URL of a .tar.gz/.rpm file or "
                    "a YUM/DNF repo. "
                    "Use --type <TYPE> to force a specific type.".
                    format(args.kernel))
    else:
        loc_type = args.type
    assert loc.type_is_valid(loc_type)

    target = data.Target(trees=args.tree,
                         arches=args.arch,
                         components=components,
                         sets=sets,
                         sources=src_files,
                         location_types=loc_type)
    return run.Base(database, target)


def main_generate(args, baserun):
    """
    Execute `run generate`

    Args:
        args:       Parsed command-line arguments.
        baserun:    Test execution data.
    """
    content = baserun.generate(description=args.description,
                               kernel_location=args.kernel,
                               lint=not args.no_lint)
    if not args.output:
        sys.stdout.write(content)
    else:
        with open(args.output, 'w') as file_handler:
            file_handler.write(content)


# pylint: disable=unused-argument
def main_print_test_cases(args, baserun):
    """
    Execute `run print-test-cases`

    Args:
        args:       Parsed command-line arguments.
        baserun:    Test execution data.
    """
    case_name_list = []
    for recipeset in baserun.recipesets_of_hosts:
        for host in recipeset:
            for suite in host.suites:
                for case in suite.cases:
                    case_name_list.append(case.name)
    for case_name in sorted(case_name_list):
        print(case_name)


def main(args):
    """Main function for the `run` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)

    if args.action == 'generate':
        main_generate(args, main_create_baserun(args, database))
    elif args.action == 'print-test-cases':
        main_print_test_cases(args, main_create_baserun(args, database))
    else:
        misc.raise_action_not_found(args.action, args.command)
