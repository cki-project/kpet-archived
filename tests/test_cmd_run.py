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
"""Test cases for run command module"""
import os
import unittest
from io import StringIO

import mock

from kpet import cmd_run, data, run, misc


class CmdRunTest(unittest.TestCase):
    """Test cases for run command module."""

    def setUp(self):
        self.dbdir = os.path.join(os.path.dirname(__file__),
                                  'assets/db/general')

    def test_generate(self):
        """
        Check the success case.
        """
        database = data.Base(self.dbdir)
        baserun = run.Base(database, set())
        content = baserun.generate(description='Foo', tree_name='rhel7',
                                   arch_name='baz', kernel_location='bar',
                                   lint=True)
        with open(os.path.join(self.dbdir, 'rhel7_rendered.xml')) as fhandle:
            content_expected = fhandle.read()
        self.assertEqual(content_expected, content)

    def test_main(self):
        """
        Check generate function is called and that ActionNotFound is
        raised when the action is not found.
        """
        mock_args = mock.Mock()
        mock_args.action = 'generate'
        mock_args.tree = 'rhel7'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = self.dbdir
        mock_args.no_lint = None
        mock_args.output = None
        mock_args.pw_cookie = None
        mock_args.description = 'description'
        mock_args.mboxes = []
        mock_args.action = 'action-not-found'
        self.assertRaises(misc.ActionNotFound, cmd_run.main, mock_args)

    def test_invalid_dbdir(self):
        """Check invalid dbdir raises an exception."""
        mock_args = mock.Mock()
        mock_args.action = 'generate'
        mock_args.tree = 'rhel7'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = '/tmp/igotgoosebutnoshoes'
        mock_args.output = None
        mock_args.pw_cookie = None
        mock_args.description = 'description'
        mock_args.mboxes = []

        with self.assertRaises(Exception):
            cmd_run.main(mock_args)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_testcases(self, mock_stdout):
        """Check invalid dbdir raises an exception."""
        mock_args = mock.Mock()
        mock_args.action = 'print-test-cases'
        mock_args.tree = 'rhel7'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = self.dbdir
        mock_args.output = None
        mock_args.pw_cookie = None
        mock_args.description = 'description'
        mock_args.mboxes = []
        mock_args.patches = []

        cmd_run.main(mock_args)

        expected = ["default/ltplite", "fs/ext4", "fs/xfs"]

        self.assertEqual(mock_stdout.getvalue().splitlines(), expected)

    def test_invalid_tree(self):
        """Check invalid tree raises an exception."""

        mock_args = mock.Mock()
        mock_args.action = 'generate'
        mock_args.tree = 'rhel0'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = self.dbdir
        mock_args.output = None
        mock_args.pw_cookie = None
        mock_args.description = 'description'
        mock_args.mboxes = []

        with self.assertRaises(Exception):
            cmd_run.main(mock_args)

    def _assert_standard_testcases(self, mock_stdout):

        self.assertEqual(
            mock_stdout.write.call_args_list[0],
            mock.call('default/ltplite'),
        )
        self.assertEqual(
            mock_stdout.write.call_args_list[2],
            mock.call('fs/ext4'),
        )
        self.assertEqual(
            mock_stdout.write.call_args_list[4],
            mock.call('fs/xfs'),
        )
