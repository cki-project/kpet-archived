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

from kpet import data, schema


class SchemaTest(unittest.TestCase):
    """Test cases for schema module."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test__get_re_error_type(self):
        """ Ensure tested method returns expected type."""
        # pylint: disable=protected-access
        exc_type = schema._get_re_error_type()

        self.assertTrue('sre_constants.error' in str(exc_type) or 're.error'
                        in str(exc_type))

    def test_invalid_exc_type(self):
        """ Ensure Invalid exc. formatting is ok. """
        inv = schema.Invalid('{}: {}', 'error', 'something failed')
        self.assertEqual(str(inv), 'error: something failed')

    def test_float(self):
        """ Test float validation."""
        try:
            schema.Float().validate(3.1415926535)
        except data.Invalid:
            self.fail('Invalid exception must not be raised here')

    def test_relativepath(self):
        """ Ensure relativepath resolves path correctly."""
        path = schema.RelativeFilePath().resolve('./')

        self.assertEqual(path, os.getcwd())

    def test_dict(self):
        """ Ensure Dict validates correctly. """
        testdict = schema.Dict(schema.String())
        with self.assertRaises(schema.Invalid):
            testdict.validate({0: 'the key is not string so this fails'})

        with self.assertRaises(schema.Invalid):
            testdict.validate({'valid key': 0})

    def test_struct_init(self):
        """ Ensure struct sanitizes required to {} and that empty
            struct validates {}."""
        self.assertEqual(schema.Struct().required, {})

        try:
            schema.Struct().validate({})
        except data.Invalid:
            self.fail('Invalid exception must not be raised here')

    def test_struct_validate_required(self):
        """ Ensure that Struct.validate() checks for required items."""
        test_struct = schema.Struct(required={'test': schema.String()})
        with self.assertRaises(schema.Invalid):
            test_struct.validate({'0': 1})

    def test_struct_validate(self):
        """ Ensure that Struct.validate() checks for optional items."""
        test_struct = schema.Struct(optional={'test': schema.String()})
        with self.assertRaises(schema.Invalid):
            test_struct.validate({'test': 1})

    def test_struct_validate_list_min_len(self):
        """ Ensure that Struct.validate() checks for too short lists."""
        test_struct = schema.Struct(
            optional={'test': schema.List(schema.String(), min_len=1)}
        )
        with self.assertRaises(schema.Invalid):
            test_struct.validate({'test': []})
