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
from kpet import run, utils, data, exceptions


class RunTest(unittest.TestCase):
    """Test cases for run module."""
    def test_generate(self):
        """
        Check the success case, if it raises the proper exception when
        the type is not found and if it saves the output in a file instead
        printing it on stdout.
        """
        template_params = {
            'DESCRIPTION': 'Foo',
            'KURL': 'bar',
            'ARCH': 'baz',
        }
        dbdir = os.path.join(os.path.dirname(__file__), 'assets')
        database = data.Base(dbdir)
        template = utils.get_jinja_template('rhel7', dbdir)
        with mock.patch('sys.stdout') as mock_stdout:
            run.generate(template, template_params, [], database, None)
        with open(os.path.join(dbdir, 'rhel7_rendered.xml')) as file_handler:
            content_expected = file_handler.read()
        self.assertEqual(
            mock.call(content_expected),
            mock_stdout.write.call_args_list[0],
        )

        tmpfile = tempfile.mktemp()
        run.generate(template, template_params, [], database, tmpfile)
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
        mock_jinja_template = mock.Mock()
        mock_args = mock.Mock()
        mock_args.action = 'generate'
        mock_args.tree = 'rhel7'
        mock_args.kernel = 'kernel'
        mock_args.arch = 'arch'
        mock_args.db = os.path.join(os.path.dirname(__file__), 'assets')
        mock_args.output = None
        mock_args.pw_cookie = None
        mock_args.description = 'description'
        mock_args.mboxes = []
        with mock.patch('kpet.run.generate') as mock_generate:
            with mock.patch('kpet.utils.get_jinja_template',
                            mock_jinja_template):
                run.main(mock_args)
                mock_generate.assert_called_with(
                    mock_jinja_template(),
                    {
                        'DESCRIPTION':
                        'description',
                        'ARCH': 'arch',
                        'KURL': 'kernel',
                        'TREE': 'rhel7',
                        'getenv': os.getenv,
                    },
                    [],
                    mock.ANY,
                    None,
                    None
                )

        mock_args.action = 'action-not-found'
        self.assertRaises(exceptions.ActionNotFound, run.main, mock_args)
