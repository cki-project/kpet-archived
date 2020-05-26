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
import sys
import traceback
from kpet import cmd_run, cmd_tree, cmd_arch, cmd_component, cmd_set, \
                 cmd_variable, cmd_patch
from kpet import misc


def exec_command(args, commands):
    """Call the associated command handler"""
    try:
        command_name = args.command if args.command is not None else "help"
        command = commands[command_name]
    except KeyError:
        print('Not implemented yet', file=sys.stderr)
        return
    try:
        command[0](*command[1:])
    except SystemExit:
        pass


def main(args=None):
    """Entry point for kpet tool"""
    description = "KPET - Kernel Patch-Evaluated Testing"
    common_parser = argparse.ArgumentParser(add_help=False)
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug (backtrace) output on error')
    parser.add_argument(
        '--db',
        help='Location of database of kernel trees and tests, default "."',
        default='.',
    )
    cmds_parser = parser.add_subparsers(title="Command", dest="command")

    cmd_run.build(cmds_parser, common_parser)
    cmd_tree.build(cmds_parser, common_parser)
    cmd_arch.build(cmds_parser, common_parser)
    cmd_component.build(cmds_parser, common_parser)
    cmd_set.build(cmds_parser, common_parser)
    cmd_variable.build(cmds_parser, common_parser)
    cmd_patch.build(cmds_parser, common_parser)

    args = parser.parse_args(args)

    commands = {
        'help': [parser.print_help],
        'run': [cmd_run.main, args],
        'tree': [cmd_tree.main, args],
        'arch': [cmd_arch.main, args],
        'component': [cmd_component.main, args],
        'set': [cmd_set.main, args],
        'variable': [cmd_variable.main, args],
        'patch': [cmd_patch.main, args],
    }
    try:
        exec_command(args, commands)
    except misc.ActionNotFound:
        print('Error: No action specified', file=sys.stderr)
        parser.print_help()
        parser.print_help(file=sys.stderr)
    except Exception as exc:  # pylint: disable=broad-except
        if args.debug:
            traceback.print_exc(file=sys.stderr)
            print("", file=sys.stderr)
        # The actual exception thrown won't necessarily make much
        # sense (too generic), so print all the context recursively so
        # that the user understand what exactly has happened.
        print(misc.format_exception_stack(exc), file=sys.stderr)
        sys.exit(1)
