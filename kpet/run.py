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
from kpet.exceptions import ActionNotFound
from kpet import utils


def generate(template_content, kernel, output, arch, description):
    """
    Generate an xml output compatible with beaker.
    Args:
        template_content: Beaker xml with variables to be replaced
        kernel:           URL of a kernel built
        output:           Output file where beaker xml will be rendered
        arch:             Architecture e.g. x86_64, ppc64, etc
        description:      String used as whiteboard on beaker xml
    """
    content = template_content.format(
        DESCRIPTION=escape(description),
        ARCH_RAW=escape(arch),
        ARCH_ATTR=quoteattr(arch),
        KURL=quoteattr(kernel),
    )
    if not output:
        print(content)
    else:
        with open(output, 'w') as file_handler:
            file_handler.write(content)


def main(args):
    """Main function for the `run` command"""
    if args.action == 'generate':
        template_content = utils.get_template_content(args.tree, args.db)
        generate(template_content, args.kernel, args.output, args.arch,
                 args.description)
    else:
        raise ActionNotFound(
            'Action: "{}" not found in command "{}"'.format(
                args.action,
                args.command
            )
        )
