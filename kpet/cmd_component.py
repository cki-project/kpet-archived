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
"""The "component" command"""
import re

from kpet import misc, data, cmd_misc


def build(cmds_parser, common_parser):
    """Build the argument parser for the component command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        "component",
        help='Build component',
    )
    list_parser = action_subparser.add_parser(
        "list",
        help='List recognized build components.',
        parents=[common_parser],
    )
    list_parser.add_argument('regex', nargs='?', default=None,
                             help='Regular expression fully matching '
                                  'names of components to output.')


def main(args):
    """Main function for the `component` command"""
    if not data.Base.is_dir_valid(args.db):
        misc.raise_invalid_database(args.db)
    database = data.Base(args.db)
    if args.action == 'list':
        regex = re.compile(args.regex or ".*")
        max_name_length = max((len(k) for k in database.components), default=0)
        for name, description in sorted(database.components.items(),
                                        key=lambda i: i[0]):
            if regex.fullmatch(name):
                print(f"{name: <{max_name_length}} {description}")
    else:
        misc.raise_action_not_found(args.action, args.command)
