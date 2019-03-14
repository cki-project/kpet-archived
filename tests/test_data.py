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
        path2assets = os.path.join(os.path.dirname(__file__),
                                   'assets/db/general')
        shutil.copytree(path2assets, self.tmpdir)

        suite = os.path.join(self.tmpdir, 'suites/default/index.yaml')

        with open(suite, 'r') as fhandle:
            mydata = fhandle.read()
            mydata = mydata.replace('pattern: .*', 'pattern: .*[')

            with open(suite, 'a+') as fhandle2:
                fhandle2.write(mydata)

        with self.assertRaises(data.Invalid):
            data.Base(self.tmpdir)


class DataPatternTest(unittest.TestCase):
    """Pattern tests"""

    # pylint: disable=invalid-name
    # (matching unittest conventions)

    def assertPositiveMatch(self, pattern_data, **target_kwargs):
        """
        Assert a positive pattern matches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertTrue(data.PositivePattern(pattern_data).
                        matches(data.Target(**target_kwargs)))

    def assertPositiveMismatch(self, pattern_data, **target_kwargs):
        """
        Assert a positive pattern mismatches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertFalse(data.PositivePattern(pattern_data).
                         matches(data.Target(**target_kwargs)))

    def assertNegativeMatch(self, pattern_data, **target_kwargs):
        """
        Assert a negative pattern matches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertTrue(data.NegativePattern(pattern_data).
                        matches(data.Target(**target_kwargs)))

    def assertNegativeMismatch(self, pattern_data, **target_kwargs):
        """
        Assert a negative pattern mismatches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertFalse(data.NegativePattern(pattern_data).
                         matches(data.Target(**target_kwargs)))

    def test_empty(self):
        """Check empty patterns match anything"""
        self.assertPositiveMatch({})
        self.assertNegativeMatch({})

        self.assertPositiveMatch({}, sources=set())
        self.assertPositiveMatch({}, sources={"a"})
        self.assertNegativeMatch({}, sources=set())
        self.assertNegativeMatch({}, sources={"a"})

        self.assertPositiveMatch({}, trees=set())
        self.assertPositiveMatch({}, trees={"a"})
        self.assertNegativeMatch({}, trees=set())
        self.assertNegativeMatch({}, trees={"a"})

        self.assertPositiveMatch({}, arches=set())
        self.assertPositiveMatch({}, arches={"a"})
        self.assertNegativeMatch({}, arches=set())
        self.assertNegativeMatch({}, arches={"a"})

        self.assertPositiveMatch({}, sources=set(), trees=set())
        self.assertPositiveMatch({}, sources=set(), trees={"a"})
        self.assertPositiveMatch({}, sources={"a"}, trees=set())
        self.assertPositiveMatch({}, sources={"a"}, trees={"a"})
        self.assertNegativeMatch({}, sources=set(), trees=set())
        self.assertNegativeMatch({}, sources=set(), trees={"a"})
        self.assertNegativeMatch({}, sources={"a"}, trees=set())
        self.assertNegativeMatch({}, sources={"a"}, trees={"a"})

    def test_positive_specific_sources(self):
        """Check positive patterns with specific_sources match correctly"""
        self.assertPositiveMismatch(dict(specific_sources=True),
                                    sources=set())
        self.assertPositiveMismatch(dict(specific_sources=True, sources="a"),
                                    sources=set())

        self.assertPositiveMismatch(dict(specific_sources=False),
                                    sources={"a"})
        self.assertPositiveMismatch(dict(specific_sources=False, sources="a"),
                                    sources={"a"})
        self.assertPositiveMismatch(dict(specific_sources=False, sources="b"),
                                    sources={"a"})

        self.assertPositiveMatch(dict(specific_sources=False),
                                 sources=set())
        self.assertPositiveMatch(dict(specific_sources=False, sources="a"),
                                 sources=set())

        self.assertPositiveMatch(dict(specific_sources=True),
                                 sources={"a"})
        self.assertPositiveMatch(dict(specific_sources=True, sources="a"),
                                 sources={"a"})
        self.assertPositiveMismatch(dict(specific_sources=True, sources="b"),
                                    sources={"a"})

    def test_negative_specific_sources(self):
        """Check negative patterns with specific_sources match correctly"""
        self.assertNegativeMismatch(dict(specific_sources=False),
                                    sources=set())
        self.assertNegativeMismatch(dict(specific_sources=False, sources="a"),
                                    sources=set())

        self.assertNegativeMismatch(dict(specific_sources=True),
                                    sources={"a"})
        self.assertNegativeMismatch(dict(specific_sources=True, sources="a"),
                                    sources={"a"})
        self.assertNegativeMismatch(dict(specific_sources=True, sources="b"),
                                    sources={"a"})

        self.assertNegativeMatch(dict(specific_sources=True),
                                 sources=set())
        self.assertNegativeMatch(dict(specific_sources=True, sources="a"),
                                 sources=set())

        self.assertNegativeMatch(dict(specific_sources=False),
                                 sources={"a"})
        self.assertNegativeMismatch(dict(specific_sources=False, sources="a"),
                                    sources={"a"})
        self.assertNegativeMatch(dict(specific_sources=False, sources="b"),
                                 sources={"a"})

    def test_positive_two_params(self):
        """Check two-parameter positive patterns match correctly"""
        self.assertPositiveMatch(dict(sources="a", trees="A"),
                                 sources=set(), trees=set())
        self.assertPositiveMatch(dict(sources="a", trees="A"),
                                 sources=set(), trees={"A"})
        self.assertPositiveMatch(dict(sources="a", trees="A"),
                                 sources={"a"}, trees=set())
        self.assertPositiveMatch(dict(sources="a", trees="A"),
                                 sources={"a"}, trees={"A"})

        self.assertPositiveMismatch(dict(sources="a", trees="A"),
                                    sources={"a"}, trees={"B"})
        self.assertPositiveMismatch(dict(sources="a", trees="A"),
                                    sources={"b"}, trees={"A"})
        self.assertPositiveMismatch(dict(sources="a", trees="A"),
                                    sources={"b"}, trees={"B"})

    def test_negative_two_params(self):
        """Check two-parameter negative patterns match correctly"""
        self.assertNegativeMatch(dict(sources="a", trees="A"),
                                 sources=set(), trees=set())
        self.assertNegativeMismatch(dict(sources="a", trees="A"),
                                    sources=set(), trees={"A"})
        self.assertNegativeMismatch(dict(sources="a", trees="A"),
                                    sources={"a"}, trees=set())
        self.assertNegativeMismatch(dict(sources="a", trees="A"),
                                    sources={"a"}, trees={"A"})

        self.assertNegativeMismatch(dict(sources="a", trees="A"),
                                    sources={"a"}, trees={"B"})
        self.assertNegativeMismatch(dict(sources="a", trees="A"),
                                    sources={"b"}, trees={"A"})
        self.assertNegativeMatch(dict(sources="a", trees="A"),
                                 sources={"b"}, trees={"B"})

    def test_positive_multi_value(self):
        """Check positive patterns match multiple values correctly"""
        self.assertPositiveMatch(dict(sources="a"), sources={"a", "a"})
        self.assertPositiveMatch(dict(sources="a"), sources={"a", "b"})
        self.assertPositiveMismatch(dict(sources="a"), sources={"b", "b"})
        self.assertPositiveMismatch(dict(sources="b"), sources={"a", "a"})
        self.assertPositiveMatch(dict(sources="b"), sources={"a", "b"})
        self.assertPositiveMatch(dict(sources="b"), sources={"b", "b"})

    def test_negative_multi_value(self):
        """Check negative patterns match multiple values correctly"""
        self.assertNegativeMismatch(dict(sources="a"), sources={"a", "a"})
        self.assertNegativeMismatch(dict(sources="a"), sources={"a", "b"})
        self.assertNegativeMatch(dict(sources="a"), sources={"b", "b"})
        self.assertNegativeMatch(dict(sources="b"), sources={"a", "a"})
        self.assertNegativeMismatch(dict(sources="b"), sources={"a", "b"})
        self.assertNegativeMismatch(dict(sources="b"), sources={"b", "b"})

    def test_positive_multi_regex(self):
        """Check positive multi-regex patterns match correctly"""
        self.assertPositiveMatch(dict(sources=["a", "a"]), sources={"a"})
        self.assertPositiveMatch(dict(sources=["a", "b"]), sources={"a"})
        self.assertPositiveMismatch(dict(sources=["b", "b"]), sources={"a"})
        self.assertPositiveMismatch(dict(sources=["a", "a"]), sources={"b"})
        self.assertPositiveMatch(dict(sources=["a", "b"]), sources={"b"})
        self.assertPositiveMatch(dict(sources=["b", "b"]), sources={"b"})

    def test_negative_multi_regex(self):
        """Check negative multi-regex patterns match correctly"""
        self.assertNegativeMismatch(dict(sources=["a", "a"]), sources={"a"})
        self.assertNegativeMismatch(dict(sources=["a", "b"]), sources={"a"})
        self.assertNegativeMatch(dict(sources=["b", "b"]), sources={"a"})
        self.assertNegativeMatch(dict(sources=["a", "a"]), sources={"b"})
        self.assertNegativeMismatch(dict(sources=["a", "b"]), sources={"b"})
        self.assertNegativeMismatch(dict(sources=["b", "b"]), sources={"b"})
