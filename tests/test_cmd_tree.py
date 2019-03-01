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
"""Test cases for tree command module"""
import os
import unittest
import mock
from kpet import exceptions
from kpet import cmd_tree


class CmdTreeTest(unittest.TestCase):
    """Test cases for tree command module."""
    def test_list(self):
        """
        Check the proper exception is raised when action is not found, and if
        an exception is raised when the database directory is invalid.
        """
        dbdir = os.path.join(os.path.dirname(__file__), 'assets')
        mock_args = mock.Mock()
        mock_args.db = dbdir
        self.assertRaises(exceptions.ActionNotFound, cmd_tree.main, mock_args)
        mock_args.action = 'list'
        with mock.patch('sys.stdout') as mock_stdout:
            cmd_tree.main(mock_args)
        expected = [
            mock.call('rhel7'),
            mock.call('\n'),
            mock.call('rhel8'),
            mock.call('\n'),
        ]
        self.assertListEqual(
            expected,
            mock_stdout.write.call_args_list,
        )
        mock_args.db = '/notfounddir'
        self.assertRaises(Exception, cmd_tree.main, mock_args)
