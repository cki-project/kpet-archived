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
from __future__ import print_function
from xml.sax.saxutils import escape, quoteattr
from kpet.exceptions import ActionNotFound, ParameterNotFound
from kpet import utils


def generate(args):
    """Generate an xml output compatible with beaker"""
    if not args.db:
        raise ParameterNotFound('--db is required')
    template_content = utils.get_template_content(args.tree, args.db)
    content = template_content.format(
        DESCRIPTION=escape(args.description),
        ARCH_RAW=escape(args.arch),
        ARCH_ATTR=quoteattr(args.arch),
        KURL=quoteattr(args.kernel),
    )
    if not args.output:
        print(content)
    else:
        with open(args.output, 'w') as file_handler:
            file_handler.write(content)


def main(args):
    """Main function for the `run` command"""
    if args.action == 'generate':
        generate(args)
    else:
        raise ActionNotFound(
            'Action: "{}" not found in command "{}"'.format(
                args.action,
                args.command
            )
        )
