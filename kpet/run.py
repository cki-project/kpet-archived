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
import tempfile
import shutil
from xml.sax.saxutils import escape, quoteattr
from kpet import utils, targeted


def get_test_cases(patches, dbdir):
    """
    Return test cases by querying layout according list of patch files.
    Args:
        patches: List of patches, they can be local files or remote urls
        dbdir:   Path to the kpet-db
    """
    tmpdir = tempfile.mkdtemp(suffix='kpet')
    try:
        patches = utils.patch2localfile(patches, tmpdir)
        src_files = targeted.get_src_files(patches)
        return sorted(targeted.get_test_cases(src_files, dbdir))
    finally:
        shutil.rmtree(tmpdir)


def print_test_cases(patches, dbdir):
    """
    Print test cases by querying layout according list of patch files.
    Args:
        patches: List of patches, they can be local files or remote urls
        dbdir:   Path to the kpet-db
    """
    for test_case in get_test_cases(patches, dbdir):
        print(test_case)


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
    elif args.action == 'print-test-cases':
        print_test_cases(args.patches, args.db)
    else:
        utils.raise_action_not_found(args.action, args.command)
