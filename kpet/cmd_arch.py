# Copyright (c) 2019 Red Hat, Inc. All rights reserved. This copyrighted
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
"""The "arch" command"""
from kpet import misc, data, cmd_misc


def build(cmds_parser, common_parser):
    """Build the argument parser for the arch command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        "arch",
        help='Architecture to test on, default action "list"',
    )
    action_subparser.add_parser(
        "list",
        help='Output a list of known architecture names',
        parents=[common_parser],
    )


def main(args):
    """Main function for the `arch` command"""
    if not data.Base.is_dir_valid(args.db):
        raise Exception("\"{}\" is not a database directory".format(args.db))
    database = data.Base(args.db)
    if args.action == 'list':
        for arch in sorted(database.arches):
            print(arch)
    else:
        misc.raise_action_not_found(args.action, args.command)
