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
"""The "set" command"""
from kpet import misc, data, cmd_misc


def build(cmds_parser, common_parser):
    """Build the argument parser for the set command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        "set",
        help='Test set, default action "list".',
    )
    action_subparser.add_parser(
        "list",
        help='List available test sets.',
        parents=[common_parser],
    )


def main(args):
    """Main function for the `set` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)
    if args.action == 'list':
        max_name_length = max((len(k) for k in database.sets), default=0)
        for name, description in sorted(database.sets.items(),
                                        key=lambda i: i[0]):
            print(f"{name: <{max_name_length}} {description}")
    else:
        misc.raise_action_not_found(args.action, args.command)
