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
        self.assertRaises(SystemExit, parser.parse_args, ['run', 'generate'])

        args = parser.parse_args(
            ['run', 'generate', '-t', 'foo', '-k', 'bar', 'mbox1', 'mbox2']
        )
        self.assertEqual('run', args.command)
        self.assertEqual('generate', args.action)
        self.assertEqual('foo', args.tree)
        self.assertEqual('bar', args.kernel)
        self.assertListEqual(['mbox1', 'mbox2'], args.mboxes)
