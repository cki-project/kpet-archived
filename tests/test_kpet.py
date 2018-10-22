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
"""Test cases for main module"""
import unittest
import argparse
import mock
import kpet


class ArgumentParserTest(unittest.TestCase):
    """Test cases for command line parsing."""
    def test_build_tree_command(self):
        """Test building the tree command."""
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_tree_command(cmd_parser, common_parser)
        args = parser.parse_args(['tree', 'list'])
        self.assertEqual('tree', args.command)
        self.assertEqual('list', args.action)

    def test_build_arch_command(self):
        """Test building the arch command."""
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_arch_command(cmd_parser, common_parser)
        args = parser.parse_args(['arch', 'list'])
        self.assertEqual('arch', args.command)
        self.assertEqual('list', args.action)

    def test_build_run_command(self):
        """Test building the run command."""
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_run_command(cmd_parser, common_parser)
        with mock.patch('sys.stderr', mock.Mock()):
            # Hide stderr output
            self.assertRaises(SystemExit,
                              parser.parse_args, ['run', 'generate'])

        args = parser.parse_args(
            ['run', 'generate', '-t', 'foo', '-k', 'bar', 'mbox1', 'mbox2']
        )
        self.assertEqual('run', args.command)
        self.assertEqual('generate', args.action)
        self.assertEqual('foo', args.tree)
        self.assertEqual('bar', args.kernel)
        self.assertListEqual(['mbox1', 'mbox2'], args.mboxes)

    def test_exec_command(self):
        """
        Check the success case, command in question raises an exception,
        that SystemExit is ignored and when a command is not implemented prints
        `Not implemented yet` on stdout
        """
        mock_command = mock.Mock()
        commands = {
            'foobar': [mock_command, 'foo', 'bar'],
        }
        mock_args = mock.Mock()
        mock_args.command = 'foobar'
        kpet.exec_command(mock_args, commands)
        mock_command.assert_called_with('foo', 'bar')

        mock_command.reset_mock()
        mock_command.side_effect = ValueError
        with mock.patch('sys.stderr', mock.Mock()):
            # Hide stderr output
            self.assertRaises(
                ValueError,
                kpet.exec_command,
                mock_args, commands
            )

        mock_command.reset_mock()
        mock_command.side_effect = SystemExit
        kpet.exec_command(mock_args, commands)
        mock_command.assert_called_with('foo', 'bar')

        mock_args.command = 'barfoo'
        mock_command.reset_mock()
        with mock.patch('sys.stdout') as mock_stdout:
            kpet.exec_command(mock_args, commands)
            self.assertEqual(
                mock_stdout.write.call_args_list[0],
                mock.call('Not implemented yet'),
            )
