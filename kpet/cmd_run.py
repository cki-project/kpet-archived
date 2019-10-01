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
from kpet import misc, patch, data, run, cmd_misc


def build_target(parser, generate):
    """
    Add target-specifying arguments to a "run" sub-command parser.

    Args:
        parser: The parser to add arguments to.
        generate: True, if the options should have restrictions imposed on
                  targets by template generation (kpet.run.Base.generate()).
                  False if not.
    """
    parser.add_argument(
        '--cookies',
        metavar='FILE',
        default=None,
        help='Cookies to send when downloading patches, Netscape-format file.'
    )
    parser.add_argument(
        '-g',
        '--group',
        help='Name of the job group',
        default='cki'
    )
    parser.add_argument(
        '-t',
        '--tree',
        required=generate,
        help='Name of the specified kernel\'s tree. ' +
        'See "kpet tree list" for recognized trees.'
    )
    parser.add_argument(
        '-a',
        '--arch',
        required=generate,
        help='Architecture of the specified kernel. ' +
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
        '-k',
        '--kernel',
        required=True,
        help='Kernel location. Must be accessible by Beaker.'
    )
    generate_parser.add_argument(
        '--no-lint',
        action='store_true',
        help='Do not lint and reformat output XML'
    )
    build_target(generate_parser, generate=True)

    print_test_cases_parser = action_subparser.add_parser(
        "print-test-cases",
        help="Print test cases applicable to the patches",
        parents=[common_parser],
    )
    build_target(print_test_cases_parser, generate=False)


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
    target_trees = data.Target.ANY
    target_arches = data.Target.ANY
    target_components = data.Target.NONE
    target_sources = data.Target.ALL
    sets = None

    cookies = cookiejar.MozillaCookieJar()
    if args.cookies:
        cookies.load(args.cookies)
    if args.mboxes:
        target_sources = patch.get_src_set_from_location_set(set(args.mboxes),
                                                             cookies)
    if args.tree is not None:
        if args.tree not in database.trees:
            raise Exception("Tree \"{}\" not found".format(args.tree))
        target_trees = {args.tree}
    if args.arch is not None:
        if args.arch not in database.arches:
            raise Exception("Architecture \"{}\" not found".format(args.arch))
        if args.tree is not None and\
           args.arch not in database.trees[args.tree]['arches']:
            raise Exception("Arch \"{}\" not supported by tree \"{}\"".format(
                args.arch, args.tree))
        target_arches = {args.arch}
    if args.components is not None:
        target_components = set(x for x in database.components
                                if re.fullmatch(args.components, x))
    if args.sets is not None:
        sets = set(x for x in database.sets if re.fullmatch(args.sets, x))
        if database.sets and not sets:
            raise Exception("No test sets matched specified regular " +
                            "expression: {}".format(args.sets))

    target = data.Target(trees=target_trees,
                         arches=target_arches,
                         components=target_components,
                         # TODO: Remove after sets conversion
                         sets=data.Target.ANY,
                         sources=target_sources)
    return run.Base(database, target, sets)


def main_generate(args, baserun):
    """
    Execute `run generate`

    Args:
        args:       Parsed command-line arguments.
        baserun:    Test execution data.
    """
    content = baserun.generate(description=args.description,
                               kernel_location=args.kernel,
                               lint=not args.no_lint,
                               group=args.group)
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
