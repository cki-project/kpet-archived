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
import os

from jinja2 import Markup

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
        return sorted(targeted.get_test_cases(src_files, dbdir),
                      key=lambda e: e.testname)
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


def get_soaking_inner(test_case, tasks, is_soaking):
    """ Function called by jinja templating to add 'soaking="{val}"' based
        on the data we have from json.

        Args:
            test_case:  name of the testcase to get data for
            tasks:
            is_soaking: soaking dict from patterns.json of a test
    """
    idx = tasks.index(test_case)

    val = is_soaking[idx]

    if val in (0, 1):
        return Markup('soaking="' + str(val) + '"')

    return ''


def generate(template, template_params, patches, dbdir, output):
    """
    Generate an xml output compatible with beaker.
    Args:
        template:        Jinja template instance
        template_params: A dictionary with template parameters such as arch,
                         whiteboard description, etc.
        patches:         List of patches, can be local files or remote urls
        dbdir:           Path to the kpet-db
        output:          Output file where beaker xml will be rendered
    """
    testcases = get_test_cases(patches, dbdir)
    test_names = [t.testname for t in testcases]
    tasks = targeted.get_tasks(test_names, dbdir)

    is_soaking = [(t.soak_data if t.soak_data else '')
                  for t in testcases]

    get_soaking = lambda x: get_soaking_inner(x, tasks, is_soaking)  # noqa
    # E731: I need this wrapper, so I can unit test get_soaking_inner

    template_params['TEST_CASES'] = sorted(
        tasks
    )
    template_params['TEST_CASES_HOST_REQUIRES'] = sorted(
        targeted.get_host_requires(
            test_names,
            dbdir
        )
    )
    template_params['TEST_CASES_PARTITIONS'] = sorted(
        targeted.get_partitions(
            test_names,
            dbdir
        )
    )
    try:
        template.environment.globals['get_soaking'] = get_soaking
    except TypeError:
        # ignore this, get_soaking cannot be mocked
        pass

    content = template.render(template_params)
    if not output:
        print(content)
    else:
        with open(output, 'w') as file_handler:
            file_handler.write(content)


def main(args):
    """Main function for the `run` command"""
    if args.action == 'generate':
        template = utils.get_jinja_template(args.tree, args.db)
        template_params = {
            'DESCRIPTION': args.description,
            'ARCH': args.arch,
            'KURL': args.kernel,
            'TREE': args.tree,
            'getenv': os.getenv,
        }
        generate(template, template_params, args.mboxes, args.db, args.output)
    elif args.action == 'print-test-cases':
        print_test_cases(args.patches, args.db)
    else:
        utils.raise_action_not_found(args.action, args.command)
