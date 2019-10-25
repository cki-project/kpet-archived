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
"""The "tree" command"""
import re

from kpet import misc, data, cmd_misc


def build(cmds_parser, common_parser):
    """Build the argument parser for the tree command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        "tree",
        help='Kernel tree, default action "list".',
    )
    list_parser = action_subparser.add_parser(
        "list",
        help='List available kernel trees.',
        parents=[common_parser],
    )
    list_parser.add_argument('-a', '--arch', metavar='REGEX',
                             default=None,
                             help='Limit output to trees with architectures '
                             'matching the REGEX.')
    list_parser.add_argument('regex', nargs='?', default=None,
                             help='Regular expression fully matching '
                                  'names of trees to output.')


def main(args):
    """Main function for the `tree` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)
    if args.action == 'list':
        regex = re.compile(args.regex or ".*")
        arch_regex = re.compile(args.arch or ".*")
        tree_names = set()
        for name, value in database.trees.items():
            filtered = list(filter(arch_regex.fullmatch, value['arches']))
            if regex.fullmatch(name) and filtered:
                tree_names.add(name)

        for name in sorted(tree_names):
            print(name)
    else:
        misc.raise_action_not_found(args.action, args.command)
