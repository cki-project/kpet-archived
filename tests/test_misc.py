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
"""Test cases for misc module"""
import os
import tempfile
import shutil
import unittest
import requests
import mock
from kpet import misc


class MiscTest(unittest.TestCase):
    """Test cases for misc."""
    def setUp(self):
        """Set common attributes used later on the test cases"""
        self.root_dir = os.path.join(os.path.dirname(__file__),
                                     'assets/db/general')
        self.template_rel_path = 'templates/rhel7.xml'

    def test_patch2localfile(self):
        """
        Check remote urls are fetched and saved in local files, check local
        files are untouched and if execption is raised when request response is
        invalid.
        """
        tmpdir = tempfile.mkdtemp()
        patches = misc.patch2localfile(['/patch', '/another/patch'], tmpdir)
        self.assertListEqual(
            ['/patch', '/another/patch'],
            patches
        )
        with mock.patch('requests.get') as mock_request_get:
            response = mock.Mock()
            response.content = b'some content'
            mock_request_get.return_value = response
            patches = misc.patch2localfile(
                ['http://mypatch.org', '/localfile'],
                tmpdir
            )
            mock_request_get.assert_called_with('http://mypatch.org',
                                                cookies=None)
            with open(patches[0]) as file_handler:
                file_content = file_handler.read()
            self.assertEqual('some content', file_content)
            response.raise_for_status.side_effect = requests.HTTPError
            self.assertRaises(requests.HTTPError, misc.patch2localfile,
                              ['http://mypatch.org', '/localfile'], tmpdir)
        shutil.rmtree(tmpdir)
