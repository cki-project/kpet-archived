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
"""Test cases for utils module"""
import os
import tempfile
import shutil
import unittest
import requests
import mock
import jinja2
from kpet import utils


class UtilsTest(unittest.TestCase):
    """Test cases for utils."""
    def setUp(self):
        """Set common attributes used later on the test cases"""
        self.root_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.template_rel_path = 'templates/rhel7.xml'

    def test_patch2localfile(self):
        """
        Check remote urls are fetched and saved in local files, check local
        files are untouched and if execption is raised when request response is
        invalid.
        """
        tmpdir = tempfile.mkdtemp()
        patches = utils.patch2localfile(['/patch', '/another/patch'], tmpdir)
        self.assertListEqual(
            ['/patch', '/another/patch'],
            patches
        )
        with mock.patch('requests.get') as mock_request_get:
            response = mock.Mock()
            response.content = b'some content'
            mock_request_get.return_value = response
            patches = utils.patch2localfile(
                ['http://mypatch.org', '/localfile'],
                tmpdir
            )
            mock_request_get.assert_called_with('http://mypatch.org',
                                                cookies=None)
            with open(patches[0]) as file_handler:
                file_content = file_handler.read()
            self.assertEqual('some content', file_content)
            response.raise_for_status.side_effect = requests.HTTPError
            self.assertRaises(requests.HTTPError, utils.patch2localfile,
                              ['http://mypatch.org', '/localfile'], tmpdir)
        shutil.rmtree(tmpdir)

    def test_get_jinja_template(self):
        """
        Check the success case and if it raises the proper exception when
        the template is not found
        """
        template = utils.get_jinja_template('rhel7', self.root_dir)
        self.assertEqual(
            'rhel7.xml',
            template.name,
        )
        self.assertRaises(jinja2.exceptions.TemplateNotFound,
                          utils.get_jinja_template, 'not-found', self.root_dir)
