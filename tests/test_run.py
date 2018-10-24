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
import tempfile
import unittest
import mock
from kpet import run, utils, exceptions


class RunTest(unittest.TestCase):
    """Test cases for run module."""
    def test_generate(self):
        """
        Check the success case, if it raises the proper exception when
        the type is not found and if it saves the output in a file instead
        printing it on stdout.
        """
        mock_args = mock.Mock()
        mock_args.tree = 'rhel8'
        mock_args.description = 'Foo'
        mock_args.kernel = 'bar'
        mock_args.arch = 'baz'
        mock_args.output = ''
        mock_args.db = ''
        self.assertRaises(exceptions.ParameterNotFound, run.generate,
                          mock_args)
        mock_args.db = 'kpet'
        template_content = utils.get_template_content(mock_args.tree + '.xml')
        content_expected = template_content.format(
            DESCRIPTION=mock_args.description,
            ARCH='"{}"'.format(mock_args.arch),
            KURL='"{}"'.format(mock_args.kernel),
        )
        with mock.patch('sys.stdout') as mock_stdout:
            run.generate(mock_args)
        self.assertEqual(
            mock.call(content_expected),
            mock_stdout.write.call_args_list[0],
        )

        tmpfile = tempfile.mktemp()
        mock_args.output = tmpfile
        run.generate(mock_args)
        with open(tmpfile) as tmp_handler:
            content = tmp_handler.read()
        self.assertEqual(
            content_expected,
            content,
        )
        os.remove(tmpfile)

        mock_args.tree = 'notfound'
        self.assertRaises(utils.TemplateNotFound, run.generate, mock_args)

    def test_main(self):
        """
        Check generate function is called and that ActionNotFound is
        raised when the action is not found.
        """
        mock_args = mock.Mock()
        mock_args.action = 'generate'
        with mock.patch('kpet.run.generate') as mock_generate:
            run.main(mock_args)
            mock_generate.assert_called_with(mock_args)

        mock_args.action = 'action-not-found'
        self.assertRaises(run.ActionNotFound, run.main, mock_args)
