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
import shutil
import tempfile
import unittest

from kpet import data


class DataTest(unittest.TestCase):
    """Test cases for data module."""
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_invalid_schema(self):
        """
        Check that Object raiser Invalid exception if the schema doesn't match.
        """
        with open(os.path.join(self.tmpdir, 'index.yaml'), 'w') as fhandle:
            fhandle.write('')

        with self.assertRaises(data.Invalid):
            data.Base(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_invalid_schema2(self):
        """
        Check that Object raiser Invalid exception if the schema doesn't match.
        """
        self.tmpdir = '/tmp/assets'
        path2assets = os.path.join(os.path.dirname(__file__), 'assets')
        shutil.copytree(path2assets, self.tmpdir)

        patterns = os.path.join(self.tmpdir, 'suites/default/patterns.yaml')

        with open(patterns, 'r') as fhandle:
            mydata = fhandle.read()
            mydata = mydata.replace('pattern: .*', 'pattern: .*[')

            with open(patterns, 'a+') as fhandle2:
                fhandle2.write(mydata)

        with self.assertRaises(data.Invalid):
            data.Base(self.tmpdir)
