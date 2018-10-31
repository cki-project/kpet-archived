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
from kpet import run, utils


class RunTest(unittest.TestCase):
    """Test cases for run module."""
    def test_generate(self):
        """
        Check the success case, if it raises the proper exception when
        the type is not found and if it saves the output in a file instead
        printing it on stdout.
        """
        tree = 'rhel8'
        description = 'Foo'
        kernel = 'bar'
        arch = 'baz'
        dbdir = os.path.join(os.path.dirname(__file__), 'assets')
        template_content = utils.get_template_content(tree, dbdir)
        content_expected = template_content.format(
            DESCRIPTION=description,
            ARCH_RAW='{}'.format(arch),
            ARCH_ATTR='"{}"'.format(arch),
            KURL='"{}"'.format(kernel),
        )
        with mock.patch('sys.stdout') as mock_stdout:
            run.generate(template_content, kernel, output=None, arch=arch,
                         description=description)
        self.assertEqual(
            mock.call(content_expected),
            mock_stdout.write.call_args_list[0],
        )

        tmpfile = tempfile.mktemp()
        run.generate(template_content, kernel, arch=arch,
                     description=description, output=tmpfile)
        with open(tmpfile) as tmp_handler:
            content = tmp_handler.read()
        self.assertEqual(
            content_expected,
            content,
        )
        os.remove(tmpfile)

    def test_main(self):
        """
        Check generate function is called and that ActionNotFound is
        raised when the action is not found.
        """
        mock_get_template_content = mock.Mock()
        mock_get_template_content.return_value = 'some text'
        mock_args = mock.Mock()
        mock_args.action = 'generate'
        mock_args.tree = 'tree'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = 'db'
        mock_args.output = None
        mock_args.description = 'description'
        mock_args.mboxes = []
        with mock.patch('kpet.run.generate') as mock_generate:
            with mock.patch('kpet.utils.get_template_content',
                            mock_get_template_content):
                run.main(mock_args)
                mock_generate.assert_called_with(
                    'some text',
                    mock_args.kernel,
                    mock_args.output,
                    mock_args.arch,
                    mock_args.description,
                )

        mock_args.tree = 'notfound'
        self.assertRaises(utils.TemplateNotFound, run.main, mock_args)

        mock_args.action = 'action-not-found'
        self.assertRaises(run.ActionNotFound, run.main, mock_args)

    @mock.patch('kpet.targeted.get_test_cases')
    def test_print_test_cases(self, mock_get_test_cases):
        """
        Check get_test_cases prints the suggested test cases.
        """
        mock_get_test_cases.return_value = ['default/ltplite', 'fs/xfs']
        with mock.patch('sys.stdout') as mock_stdout:
            run.print_test_cases("", "")
        self.assertEqual('default/ltplite',
                         mock_stdout.write.call_args_list[0][0][0])
        self.assertEqual('fs/xfs',
                         mock_stdout.write.call_args_list[2][0][0])
