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
import argparse
import os
import sys
import logging
from kpet import cmd_run, cmd_tree, cmd_arch, cmd_set


def exec_command(args, commands):
    """Call the associated command handler"""
    try:
        command = commands[args.command]
    except KeyError:
        print('Not implemented yet', file=sys.stderr)
        return
    try:
        command[0](*command[1:])
    except SystemExit:
        pass
    except:  # noqa: E731 don't use bare except pylint:disable=bad-option-value
        logging.error('While executing command "%s"', args.command)
        raise


def main(args=None):
    """Entry point for kpet tool"""
    logging.basicConfig(format="%(created)10.6f:%(levelname)s:%(message)s")
    logging.getLogger().setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
    description = "KPET - Kernel Patch-Evaluated Testing"
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--verbose', '-v', action='count')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--db',
        help='Location of database of kernel trees and tests, default "."',
        default='.',
    )
    cmds_parser = parser.add_subparsers(title="Command", dest="command")

    cmd_run.build(cmds_parser, common_parser)
    cmd_tree.build(cmds_parser, common_parser)
    cmd_arch.build(cmds_parser, common_parser)
    cmd_set.build(cmds_parser, common_parser)

    args = parser.parse_args(args)
    commands = {
        'help': [parser.print_help],
        'run': [cmd_run.main, args],
        'tree': [cmd_tree.main, args],
        'arch': [cmd_arch.main, args],
        'set': [cmd_set.main, args],
    }
    exec_command(args, commands)
