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
"""The "patch" command"""
import http.cookiejar as cookiejar

from kpet import misc, cmd_misc, patch


def build(cmds_parser, common_parser):
    """Build the argument parser for the patch command"""
    _, action_subparser = cmd_misc.build(
        cmds_parser,
        common_parser,
        "patch",
        help='Patch',
    )
    list_parser = action_subparser.add_parser(
        "list-files",
        help='List files changed by supplied patches.',
        parents=[common_parser],
    )
    list_parser.add_argument(
        '--cookies',
        metavar='FILE',
        default=None,
        help='Cookies to send when downloading patches, Netscape-format file.'
    )
    list_parser.add_argument(
        'mboxes',
        metavar='MBOX',
        nargs='*',
        default=[],
        help='URL/path of a mailbox with patches'
    )


def main(args):
    """Main function for the `patch` command"""
    if args.action == 'list-files':
        cookies = cookiejar.MozillaCookieJar()
        if args.cookies:
            cookies.load(args.cookies)
        src_set = patch.get_src_set_from_location_set(args.mboxes, cookies)
        for src in sorted(src_set):
            print(src)
    else:
        misc.raise_action_not_found(args.action, args.command)
