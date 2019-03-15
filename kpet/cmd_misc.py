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
"""Miscellaneous command-related definitions"""


# (argparse uses help as parameter) pylint: disable=redefined-builtin
def build(cmds_parser, common_parser, name, help):
    """Build a new command argument with its corresponding action subparser"""
    cmd_parser = cmds_parser.add_parser(
        name,
        help=help,
        parents=[common_parser],
    )
    action_subparser = cmd_parser.add_subparsers(
        title="action",
        dest="action",
    )
    return cmd_parser, action_subparser
