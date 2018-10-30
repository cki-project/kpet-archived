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
import logging
from xml.sax.saxutils import escape, quoteattr
from kpet.exceptions import ActionNotFound
from kpet import utils


def get_test_cases(l_patch, f_layout):
    """Get test cases by querying layout according list of patch files"""
    l_srcfiles = utils.smart_get_src_files(l_patch)
    if not l_srcfiles:
        logging.info("No source file updated")
        return []

    l_cases = utils.smart_get_test_cases(l_srcfiles, f_layout)
    if l_cases is None:
        logging.error("Fail to get test cases")
        return None

    return l_cases


def generate(args):
    """Generate an xml output compatible with beaker OR output test cases"""
    # Output test cases only
    if args.output_testcase:
        if not args.mboxes:
            logging.error("No patch file specified")
            return 1

        if not args.layout:
            logging.error("No layout file specified")
            return 1

        l_tc = get_test_cases(args.mboxes, args.layout)
        if l_tc is None:
            logging.error("No test case found")
            return 1

        print(','.join(l_tc))
        return 0

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

    return 0


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
