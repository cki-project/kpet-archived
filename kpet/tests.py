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
"""Module where the `tree` command is implemented"""
from __future__ import print_function

import json
import logging
import os

from six import moves
import gitlab


from kpet import utils


class TestEnabler(object):
    """ A class to enable/disable tests by modyfying layout/layout.json."""
    # pylint: disable=useless-object-inheritance
    def __init__(self, db_path):
        # path to layout file of kpet-db
        self.layout_file = os.path.join('layout', 'layout.json')
        self.layout_path = os.path.join(db_path, self.layout_file)

        # the parsed json layout.json
        self.obj = None
        # a portion of layout.json - enabled testsuites
        self.testsuites = None
        # a portion of layout.json - disabled testsuites
        self.testsuites_disabled = None

        # gitlab project, to be used to change remote file if
        # 'branch' isn't empty
        self.project = None

        gitlab_url = os.environ['GITLAB_URL']
        private_token = os.environ['GITLAB_PRIVATE_TOKEN']

        self.gitlab_instance = gitlab.Gitlab(gitlab_url,
                                             private_token=private_token,
                                             api_version=str(4))

    def get_testsuites(self):
        """ Load layout.json and populate testsuites, testsuites_disabled class
            attributes.
        """

        with open(self.layout_path, 'r') as handle:
            self.obj = json.load(handle)
        assert self.obj['schema']['version'] == 1

        # load a portion of the obj parsed json
        self.testsuites = self.obj['testsuites']

        # create empty testsuites_disabled if necessary
        try:
            self.testsuites_disabled = self.obj['testsuites_disabled']
        except KeyError:
            self.testsuites_disabled = {}

    def check_test_exists(self, testname):
        """ Raise error if the testname is not present in parsed json."""
        if testname not in self.testsuites.keys() and testname not in \
                self.testsuites_disabled.keys():
            raise RuntimeError('Test not found')

    def move_test(self, ffrom, move_to, testname):
        """ Move test from one dict to another, then set self.obj.

        """
        # add test to disabled
        move_to[testname] = ffrom[testname]

        # remove test from ffrom dict
        ffrom.pop(testname)

        self.obj['testsuites'] = self.testsuites
        self.obj['testsuites_disabled'] = self.testsuites_disabled

    def enable_disable_test(self, testname, action):
        """
        Enable or disable a test by modifying layout/layout.json of set KPET-db
        db_path.
        This method checks if test exists, is already disabled/enabled.
        If all is good, the test is moved from disabled to enable or
        vice-versa. As a result, the json layout file is recreated.

        Args:
            testname: a short name of the test to enable/disable
            action: str - 'enable' or 'disable'
        """

        self.check_test_exists(testname)

        # let user know
        logging.info('%s-ing "%s" testcase', action, testname)

        ffrom = self.testsuites_disabled if action == 'enable' else \
            self.testsuites

        move_to = self.testsuites if action == 'enable' else \
            self.testsuites_disabled

        if testname in move_to.keys() or testname not in ffrom.keys():
            logging.warning('Test already %sd', action)
            return

        # enable test by moving it from testsuites_disabled to testsuites
        self.move_test(ffrom, move_to, testname)

        # write changes: recreate file layout/layout.json
        with open(self.layout_path, 'w') as handle:
            json.dump(self.obj, handle, indent=4)
            handle.write('\n')

    def remote_init(self):
        """ Pull GITLAB_URL and GITLAB_PRIVATE_TOKEN from env to create gitlab
            object instance, then get 'cki-project/kpet-db' project.

            NOTE: the gitlab import is kept here, so it's possible to test it.

            Raises: ImportError if we don't have gitlab.
        """

        self.project = self.gitlab_instance.projects.get('cki-project/kpet-db')

    def get_remote_file(self, branch, ffile):
        """ Download a file from <branch> of a remote project set in
            remote_init().
        Args:
            branch: A branch to use as ref
            ffile:  A path to a file to download

        Returns: file content

        """
        ffile = self.project.files.get(file_path=ffile, ref=branch)

        return ffile

    def create_update_commit(self, branch, commit_message, ffile, content):
        """
        Create an update commit on a branch.

        Args:
            branch:         The branch to use as ref
            commit_message: The message of the newly created commit
            ffile:          A path to the file to update on branch
            content:        The new ffile content


            title:   String to use as the commit message title.
        """

        data = {
            'branch': branch,
            'commit_message': commit_message,
            "actions": [
                {
                    "action": "update",
                    "file_path": ffile,
                    "content": content
                },
            ]

        }
        self.project.commits.create(data)


def prompt_to_write(branch, test_enabler, ffile):
    """ Prompt user for confirmation to update remote file.

    Args:
        branch      : The branch to update with file content
        test_enabler: TestEnabler instance
        ffile       : A file with the update content

    """
    while True:
        choice = moves.input('Push to remote [y/n]?').lower()
        if choice == 'y':
            msg = "update {}".format(test_enabler.layout_file)
            with open(ffile, 'r') as handle:
                test_enabler.create_update_commit(branch, msg,
                                                  test_enabler.layout_file,
                                                  handle.read())

        if choice in ['y', 'n']:
            break


def do_enable(args, test_enabler):
    """ Enable or disable a test based on args.
    Args:
        args:         argaparse.Namespace (parsed arguments)
        test_enabler: TestEnabler instance
    """
    branch = args.branch
    if not branch:
        # move test locally
        test_enabler.get_testsuites()

        test_enabler.enable_disable_test(args.test, args.action)
    elif branch:
        test_enabler.remote_init()
        layout_file = test_enabler.layout_file
        str_layout = test_enabler.get_remote_file(branch, layout_file)

        with utils.tempfile_from_string(str_layout.encode()) as ffile:
            test_enabler.layout_path = ffile

            # load json (the above file we downloaded)
            test_enabler.get_testsuites()

            # move test locally on file f we downloaded
            test_enabler.enable_disable_test(args.test, args.action)

            # confirm with user and push
            prompt_to_write(branch, test_enabler, ffile)


def main(args):
    """Main function for the `tests` command"""

    if args.action in ['enable', 'disable']:
        test_enabler = TestEnabler(args.db)

        do_enable(args, test_enabler)
    else:
        logging.error('invalid arguments use kpet -h')
        utils.raise_action_not_found(args.action, args.command)
