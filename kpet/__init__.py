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
"""Main entry point and command line parsing"""
from __future__ import print_function
import argparse
import os
import logging
from kpet import run


# (argparse uses help as parameter) pylint: disable=redefined-builtin


def _build_command(cmds_parser, common_parser, name, help):
    """Build a new command argument with its corresponding action subparser"""
    cmd_parser = cmds_parser.add_parser(
        name,
        help=help,
        parents=[common_parser],
    )
    action_subparser = cmd_parser.add_subparsers(
        title="action",
        dest="action",
    )
    return cmd_parser, action_subparser


def build_run_command(cmds_parser, common_parser):
    """Build the argument parser for the run command"""
    _, action_subparser = _build_command(
        cmds_parser,
        common_parser,
        'run',
        help='Test suite run, default action "generate"',
    )
    action_parser = action_subparser.add_parser(
        "generate",
        help='Generate the information required for a test run',
        parents=[common_parser],
    )
    action_parser.add_argument(
        '-d',
        '--description',
        default='',
        help='An arbitrary text describing the run'
    )
    action_parser.add_argument(
        '-o',
        '--output',
        default=None,
        help='Path where will be saved the xml, default is stdout'
    )
    action_parser.add_argument(
        '-t',
        '--tree',
        required=True,
        help='kernel "tree" name, chosen from "tree list" output, or "MAIL"'
    )
    action_parser.add_argument(
        '-a',
        '--arch',
        default='x86_64',
        help='An architecture chosen from "arch list" output'
    )
    action_parser.add_argument(
        '--type',
        default='auto',
        choices=['auto', 'tarball-url', 'rpm-url', 'tarball-path', 'rpm-path'],
        help='Type of the kernel reference'
    )
    action_parser.add_argument(
        '-k',
        '--kernel',
        required=True,
        help='Compiled kernel'
    )
    action_parser.add_argument(
        '-c',
        '--cover-letter',
        default='no cover letter',
        help='Patch series cover letter mbox URL/path'
    )
    action_parser.add_argument(
        'mboxes',
        nargs='*',
        default=[],
        help='List of mbox URLs/paths comprising the patch series'
    )


def build_arch_command(cmds_parser, common_parser):
    """Build the argument parser for the arch command"""
    _, action_subparser = _build_command(
        cmds_parser,
        common_parser,
        "arch",
        help='Architecture to test on, default action "list"',
    )
    action_subparser.add_parser(
        "list",
        help='Output a list of known architecture names',
        parents=[common_parser],
    )


def build_tree_command(cmds_parser, common_parser):
    """Build the argument parser for the tree command"""
    _, action_subparser = _build_command(
        cmds_parser,
        common_parser,
        "tree",
        help='Kernel tree, default action "list".',
    )
    action_subparser.add_parser(
        "list",
        help='List available kernel trees.',
        parents=[common_parser],
    )


def exec_command(args, commands):
    """Call the associated command handler"""
    try:
        command = commands[args.command]
    except KeyError:
        print('Not implemented yet')
        return
    try:
        command[0](*command[1:])
    except SystemExit:
        pass
    except:  # noqa: E731 don't use bare except pylint:disable=bad-option-value
        logging.error('While executing command "%s"', args.command)
        raise


def main():
    """Entry point for kpet tool"""
    logging.basicConfig(format="%(created)10.6f:%(levelname)s:%(message)s")
    logging.getLogger().setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
    description = "KPET - Kernel Patch-Evaluated Testing"
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--verbose', '-v', action='count')
    common_parser.add_argument(
        '--db',
        help='Location of database of kernel trees and tests',
    )
    parser = argparse.ArgumentParser(description=description)
    cmds_parser = parser.add_subparsers(title="Command", dest="command")

    cmds_parser.add_parser(
        'help',
        help='show this help message and exit',
    )
    build_run_command(cmds_parser, common_parser)
    build_tree_command(cmds_parser, common_parser)
    build_arch_command(cmds_parser, common_parser)

    args = parser.parse_args()
    commands = {
        'help': [parser.print_help],
        'run': [run.main, args],
    }
    exec_command(args, commands)
