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
from kpet import tree


class TreeTest(unittest.TestCase):
    """Test cases for tree module."""
    def test_list(self):
        """
        Check the proper exception is raised when action is not found, the
        success case only listing files ending with .xml and if exception is
        raised when the `templates` folder is not found or templates is not a
        directory.
        """
        dbdir = os.path.join(os.path.dirname(__file__), 'assets')
        mock_args = mock.Mock()
        self.assertRaises(exceptions.ActionNotFound, tree.main, mock_args)
        tmpdir = tempfile.mkdtemp()
        tmp_dbdir = os.path.join(tmpdir, 'db')
        shutil.copytree(dbdir, tmp_dbdir)
        with open(os.path.join(tmp_dbdir, 'templates', 'file.txt'), 'w'):
            pass
        mock_args.db = tmp_dbdir
        mock_args.action = 'list'
        with mock.patch('sys.stdout') as mock_stdout:
            tree.main(mock_args)
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
        shutil.rmtree(tmpdir)
        mock_args.db = '/notfounddir'
        self.assertRaises(tree.TemplateDirNotFound, tree.main, mock_args)

        tmpdir = tempfile.mkdtemp()
        mock_args.db = tmpdir
        with open(os.path.join(tmpdir, 'templates'), 'w'):
            pass
        self.assertRaises(OSError, tree.main, mock_args)
        shutil.rmtree(tmpdir)
