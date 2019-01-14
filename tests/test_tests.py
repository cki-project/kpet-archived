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
"""Test cases for run module"""

import os
import unittest
import tempfile
import shutil
import mock

from kpet import exceptions
import kpet


class FakeGitLabCommits(object):
    """ A fake GitLabCommits class for purposes of this testing."""
    # pylint: disable=useless-object-inheritance,too-few-public-methods
    def __init__(self):
        self._commits = []

    def create(self, data):
        """ A fake method to create a commit."""
        self._commits.append(data)


class FakeGitLabProject(object):
    """ A fake GitLabProject class for purposes of this testing."""
    # pylint: disable=useless-object-inheritance,too-few-public-methods
    def __init__(self):
        self.commits = FakeGitLabCommits()
        self.files = FakeGitFiles()


class FakeGitFiles(object):
    """ A fake GitFiles class for purposes of this testing."""
    # pylint: disable=useless-object-inheritance,too-few-public-methods
    # pylint: disable=unused-argument,no-self-use
    def __init__(self):
        self.files = {}

    def get(self, file_path=None, ref=None):
        """ A fake method to load asset file instead of downloading it.
            Args:
                file_path: a path to a file relative to tree root
                ref:       a branch reference
        """
        path = os.path.join(os.path.dirname(__file__), 'assets', file_path)
        handle = open(path, 'r')
        content = handle.read()
        handle.close()

        return content


class FakeGitLab(object):
    """ A fake GitLab class for purposes of this testing."""
    # pylint: disable=useless-object-inheritance,too-few-public-methods
    def __init__(self):
        self.projects = {}

    def add_project(self, project_name):
        """ A fake method to add a project.
            Args:
                project_name: name of the project to add
        """
        self.projects[project_name] = FakeGitLabProject()


class TestsTest(unittest.TestCase):
    """ Test cases for tests module."""

    def setUp(self):
        """ Ensure test methods have what they need for testing."""
        os.environ.update({'GITLAB_URL': 'http://gitlab.test',
                           'GITLAB_PRIVATE_TOKEN': 'private-token'})

        dbdir = os.path.join(os.path.dirname(__file__), 'assets')
        tmpdir = tempfile.mkdtemp()
        self.tmp_dbdir = os.path.join(tmpdir, 'db')
        shutil.copytree(dbdir, self.tmp_dbdir)
        with open(os.path.join(self.tmp_dbdir, 'templates', 'file.txt'), 'w'):
            pass

    def tearDown(self):
        """ Cleanup after testing."""
        del os.environ['GITLAB_URL']
        del os.environ['GITLAB_PRIVATE_TOKEN']

    def get_standard_mock_args(self, action, testname, branch=None):
        """ Create mocked arguments for main of uut.
            Args:
                action:   'enable' or 'disable' a test
                testname: a test to enable or disable
                branch:   remote branch to update, or None to work locally
        """
        mock_args = mock.Mock()

        mock_args.db = self.tmp_dbdir
        mock_args.action = action
        mock_args.test = testname
        mock_args.branch = branch

        return mock_args

    @mock.patch('logging.error')
    def test_actions(self, mock_logging):
        """ Check the proper exception is raised when action is not found."""
        # pylint: disable=unused-argument
        mock_args = mock.Mock()
        self.assertRaises(exceptions.ActionNotFound, kpet.tests.main,
                          mock_args)

    @mock.patch('logging.warning')
    def test_disable_invalid(self, mock_logging):
        """ Ensure that disabling non-existing-test fails."""
        # pylint: disable=unused-argument
        mock_args = self.get_standard_mock_args('disable', 'non-existing-test')

        with self.assertRaises(RuntimeError):
            kpet.tests.main(mock_args)

    def test_remote(self):
        """ Ensure that main works for remote operation."""
        test_enabler = kpet.tests.TestEnabler(self.tmp_dbdir)

        test_enabler.gitlab_instance = FakeGitLab()
        test_enabler.gitlab_instance.add_project('cki-project/kpet-db')

        mock_args = self.get_standard_mock_args('disable', 'fs', 'master')

        with mock.patch('six.moves.input',
                        mock.MagicMock(name='input', side_effect=['y',
                                                                  EOFError])):
            kpet.tests.do_enable(mock_args, test_enabler)

    @mock.patch('logging.warning')
    def test_main_calls_enable(self, mock_logging):
        """Verify main() calls enable local functions it should."""
        # pylint: disable=unused-argument

        mock_args = self.get_standard_mock_args('enable', 'fs')
        kpet.tests.main(mock_args)

    @mock.patch('logging.warning')
    def test_main_calls_disable(self, mock_logging):
        """Verify main() calls disable local functions it should."""
        # pylint: disable=unused-argument

        mock_args = self.get_standard_mock_args('disable', 'fs')
        kpet.tests.main(mock_args)

    def test_create_update_commit(self):
        """ Ensure TestEnabler's remote_init() doesn't crash."""
        test_enabler = kpet.tests.TestEnabler(self.tmp_dbdir)
        test_enabler.gitlab_instance = FakeGitLab()

        test_enabler.remote_init()

    def test_move(self):
        """ Ensure that move_test() method of TestEnabler works."""
        test_enabler = kpet.tests.TestEnabler(self.tmp_dbdir)

        test_enabler.testsuites = {'data': 0}
        test_enabler.testsuites_disabled = {'data_disabled': 0}

        test_enabler.obj = {}
        test_enabler.obj['testsuites'] = {}
        test_enabler.obj['testsuites_disabled'] = {}

        ffrom = {'a': 0}
        move_to = {}

        test_enabler.move_test(ffrom, move_to, 'a')

        self.assertEqual(ffrom, {})
        self.assertEqual(move_to, {'a': 0})
        self.assertEqual(test_enabler.obj['testsuites_disabled'],
                         test_enabler.testsuites_disabled)
        self.assertEqual(test_enabler.obj['testsuites'],
                         test_enabler.testsuites)
        self.assertEqual(test_enabler.obj['testsuites_disabled'],
                         {'data_disabled': 0})
        self.assertEqual(test_enabler.obj['testsuites'],
                         {'data': 0})
