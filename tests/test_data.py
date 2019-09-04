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
            mydata = mydata.replace('maintainers:', 'maintainers: []')
            mydata = mydata.replace('- maint1', '')

            # overwrite the file, without required 'maintainers: field'
            with open(suite, 'w') as fhandle2:
                fhandle2.write(mydata)

        with self.assertRaises(data.Invalid):
            data.Base(self.tmpdir)


class DataPatternTest(unittest.TestCase):
    """Pattern tests"""

    # pylint: disable=invalid-name
    # (matching unittest conventions)

    def assertMatch(self, pattern_data, **target_kwargs):
        """
        Assert a pattern matches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertTrue(data.Pattern(pattern_data).
                        matches(data.Target(**target_kwargs)))

    def assertMismatch(self, pattern_data, **target_kwargs):
        """
        Assert a pattern mismatches.

        Args:
            pattern_data:   The data to create the pattern from.
            target_kwargs:  Keyword arguments to create the target from.
        """
        self.assertFalse(data.Pattern(pattern_data).
                         matches(data.Target(**target_kwargs)))

    def test_empty(self):
        """Check empty patterns match anything"""
        self.assertMatch({})

        self.assertMatch({}, sources=data.Target.ANY)
        self.assertMatch({}, sources=data.Target.ALL)
        self.assertMatch({}, sources=data.Target.NONE)
        self.assertMatch({}, sources={"a"})

        self.assertMatch({}, trees=data.Target.ALL)
        self.assertMatch({}, trees={"a"})

        self.assertMatch({}, arches=data.Target.ALL)
        self.assertMatch({}, arches={"a"})

        self.assertMatch({}, sources=data.Target.ANY, trees=data.Target.ANY)
        self.assertMatch({}, sources=data.Target.NONE, trees=data.Target.NONE)
        self.assertMatch({}, sources=data.Target.ALL, trees=data.Target.ALL)
        self.assertMatch({}, sources=data.Target.ALL, trees={"a"})
        self.assertMatch({}, sources={"a"}, trees=data.Target.ALL)
        self.assertMatch({}, sources={"a"}, trees={"a"})

    def test_specific_sources(self):
        """Check patterns match specific/all sources correctly"""
        self.assertMismatch({"not": dict(sources=None)},
                            sources=data.Target.ALL)
        self.assertMismatch({"not": dict(sources=None), "sources": "a"},
                            sources=data.Target.ALL)

        self.assertMismatch(dict(sources=None), sources={"a"})
        self.assertMismatch(dict(sources=[None, "a"]), sources={"a"})
        self.assertMismatch(dict(sources=[None, "b"]), sources={"a"})

        self.assertMatch(dict(sources=None), sources=data.Target.ALL)
        self.assertMatch(dict(sources=[None, "a"]), sources=data.Target.ALL)

        self.assertMatch({"not": dict(sources=None)},
                         sources={"a"})
        self.assertMatch({"not": dict(sources=None), "sources": "a"},
                         sources={"a"})
        self.assertMismatch({"not": dict(sources=None), "sources": "b"},
                            sources={"a"})

    def test_two_params(self):
        """Check two-parameter patterns match correctly"""
        self.assertMatch(dict(sources="a", trees="A"),
                         sources=data.Target.ALL, trees=data.Target.ALL)
        self.assertMatch(dict(sources="a", trees="A"),
                         sources=data.Target.ALL, trees={"A"})
        self.assertMatch(dict(sources="a", trees="A"),
                         sources=data.Target.ANY, trees=data.Target.ANY)
        self.assertMatch(dict(sources="a", trees="A"),
                         sources={"a"}, trees=data.Target.ANY)
        self.assertMatch(dict(sources="a", trees="A"),
                         sources={"a"}, trees=data.Target.ALL)
        self.assertMatch(dict(sources="a", trees="A"),
                         sources={"a"}, trees={"A"})

        self.assertMismatch(dict(sources="a", trees="A"),
                            sources={"a"}, trees={"B"})
        self.assertMismatch(dict(sources="a", trees="A"),
                            sources={"b"}, trees={"A"})
        self.assertMismatch(dict(sources="a", trees="A"),
                            sources={"b"}, trees={"B"})

    def test_multi_value(self):
        """Check patterns match multiple values correctly"""
        self.assertMatch(dict(sources="a"), sources={"a", "a"})
        self.assertMatch(dict(sources="a"), sources={"a", "b"})
        self.assertMismatch(dict(sources="a"), sources={"b", "b"})
        self.assertMismatch(dict(sources="b"), sources={"a", "a"})
        self.assertMatch(dict(sources="b"), sources={"a", "b"})
        self.assertMatch(dict(sources="b"), sources={"b", "b"})

    def test_multi_regex(self):
        """Check multi-regex patterns match correctly"""
        self.assertMatch(dict(sources={"or": ["a", "a"]}), sources={"a"})
        self.assertMatch(dict(sources={"or": ["a", "b"]}), sources={"a"})
        self.assertMismatch(dict(sources={"or": ["b", "b"]}), sources={"a"})
        self.assertMismatch(dict(sources={"or": ["a", "a"]}), sources={"b"})
        self.assertMatch(dict(sources={"or": ["a", "b"]}), sources={"b"})
        self.assertMatch(dict(sources={"or": ["b", "b"]}), sources={"b"})

    def test_not(self):
        """Check negation works"""
        self.assertMismatch({"not": {}})
        self.assertMatch({"not": {"not": {}}})
        self.assertMismatch({"not": {"trees": ".*"}}, trees={"a"})
        self.assertMatch({"not": {"not": {"trees": ".*"}}}, trees={"a"})

    def test_or(self):
        """Check disjunction works"""
        # Empty dict
        self.assertMismatch({"or": {}})
        # Empty list
        self.assertMismatch({"or": []})
        # One true in dict
        self.assertMatch({"or": dict(trees=".*")}, trees={"foo"})
        # One true in list
        self.assertMatch({"or": [dict(trees=".*")]}, trees={"foo"})
        # One false in dict
        self.assertMismatch({"or": dict(trees="bar")}, trees={"foo"})
        # One false in list
        self.assertMismatch({"or": [dict(trees="bar")]}, trees={"foo"})
        # True and false in dict
        self.assertMatch({"or": dict(trees=".*", arches="bleh")},
                         trees={"foo"}, arches={"baz"})
        # True and false in list
        self.assertMatch({"or": [dict(trees=".*"), dict(arches="bleh")]},
                         trees={"foo"}, arches={"baz"})
        # Two truths in dict
        self.assertMatch({"or": dict(trees=".*", arches="baz")},
                         trees={"foo"}, arches={"baz"})
        # Two truths in list
        self.assertMatch({"or": [dict(trees=".*"), dict(arches="baz")]},
                         trees={"foo"}, arches={"baz"})
        # Two falses in dict
        self.assertMismatch({"or": dict(trees="oof", arches="zab")},
                            trees={"foo"}, arches={"baz"})
        # Two falses in list
        self.assertMismatch({"or": [dict(trees="oof"), dict(arches="zab")]},
                            trees={"foo"}, arches={"baz"})

    def test_and(self):
        """Check conjunction works"""
        # Empty dict
        self.assertMatch({"and": {}})
        # Empty list
        self.assertMatch({"and": []})
        # One true in dict
        self.assertMatch({"and": dict(trees=".*")}, trees={"foo"})
        # One true in list
        self.assertMatch({"and": [dict(trees=".*")]}, trees={"foo"})
        # One false in dict
        self.assertMismatch({"and": dict(trees="bar")}, trees={"foo"})
        # One false in list
        self.assertMismatch({"and": [dict(trees="bar")]}, trees={"foo"})
        # True and false in dict
        self.assertMismatch({"and": dict(trees=".*", arches="bleh")},
                            trees={"foo"}, arches={"baz"})
        # True and false in list
        self.assertMismatch({"and": [dict(trees=".*"), dict(arches="bleh")]},
                            trees={"foo"}, arches={"baz"})
        # Two truths in dict
        self.assertMatch({"and": dict(trees=".*", arches="baz")},
                         trees={"foo"}, arches={"baz"})
        # Two truths in list
        self.assertMatch({"and": [dict(trees=".*"), dict(arches="baz")]},
                         trees={"foo"}, arches={"baz"})
        # Two falses in dict
        self.assertMismatch({"and": dict(trees="oof", arches="zab")},
                            trees={"foo"}, arches={"baz"})
        # Two falses in list
        self.assertMismatch({"and": [dict(trees="oof"), dict(arches="zab")]},
                            trees={"foo"}, arches={"baz"})

    def test_default_op(self):
        """Check default operation (conjunction) works"""
        # Empty dict
        self.assertMatch({})
        # Empty list
        self.assertMatch([])
        # One true in dict
        self.assertMatch(dict(trees=".*"), trees={"foo"})
        # One true in list
        self.assertMatch([dict(trees=".*")], trees={"foo"})
        # One false in dict
        self.assertMismatch(dict(trees="bar"), trees={"foo"})
        # One false in list
        self.assertMismatch([dict(trees="bar")], trees={"foo"})
        # True and false in dict
        self.assertMismatch(dict(trees=".*", arches="bleh"),
                            trees={"foo"}, arches={"baz"})
        # True and false in list
        self.assertMismatch([dict(trees=".*"), dict(arches="bleh")],
                            trees={"foo"}, arches={"baz"})
        # Two truths in dict
        self.assertMatch(dict(trees=".*", arches="baz"),
                         trees={"foo"}, arches={"baz"})
        # Two truths in list
        self.assertMatch([dict(trees=".*"), dict(arches="baz")],
                         trees={"foo"}, arches={"baz"})
        # Two falses in dict
        self.assertMismatch(dict(trees="oof", arches="zab"),
                            trees={"foo"}, arches={"baz"})
        # Two falses in list
        self.assertMismatch([dict(trees="oof"), dict(arches="zab")],
                            trees={"foo"}, arches={"baz"})

    def test_any(self):
        """Check the "ANY" target sets are handled correctly"""
        # Empty pattern
        self.assertMatch({})
        self.assertMatch({}, trees=data.Target.ANY)
        self.assertMatch({}, trees=data.Target.ANY, sources=data.Target.ANY)

        # Basic patterns
        self.assertMatch(dict(trees=None), trees=data.Target.ANY)
        self.assertMatch(dict(trees="foo"), trees=data.Target.ANY)
        self.assertMatch(dict(trees="foo", sources="bar"),
                         trees=data.Target.ANY, sources={"bar"})
        self.assertMatch(dict(trees="foo", sources="bar"),
                         trees={"foo"}, sources=data.Target.ANY)
        self.assertMismatch(dict(trees="foo", sources="bar"),
                            trees=data.Target.ANY, sources=data.Target.NONE)
        self.assertMismatch(dict(trees="foo", sources="bar"),
                            sources=data.Target.NONE)

        # Negation
        self.assertMatch({"not": dict(trees="foo")},
                         trees=data.Target.ANY)
        self.assertMatch({"not": {"not": dict(trees="foo")}},
                         trees=data.Target.ANY)
        self.assertMatch({"not": dict(trees="foo", sources="bar")},
                         trees=data.Target.ANY, sources={"baz"})
        self.assertMatch({"not": dict(trees="foo", sources="bar")},
                         trees=data.Target.ANY, sources=data.Target.NONE)
        self.assertMismatch({"not": dict(trees="foo", sources="bar")},
                            trees=data.Target.ANY, sources={"bar"})
        self.assertMismatch({"not": dict(trees="foo", sources="bar")},
                            trees=data.Target.ANY, sources=data.Target.ALL)

        # Disjunction
        self.assertMismatch({"or": dict(trees="foo", sources="bar")},
                            trees=data.Target.ANY, sources={"baz"})
        self.assertMismatch({"or": dict(trees="foo", sources="bar")},
                            trees=data.Target.ANY, sources=data.Target.NONE)
        self.assertMatch({"or": dict(trees="foo", sources="bar")},
                         trees=data.Target.ANY, sources={"bar"})
        self.assertMatch({"or": dict(trees="foo", sources="bar")},
                         trees=data.Target.ANY, sources=data.Target.ALL)

        # A complex real-life case
        self.assertMatch(dict(sets={"or": ["net", "kt1", "debug"]},
                              trees={"not": {"or": ["rhel5.*"]}},
                              sources={"or": [
                                  "include/net/tcp.*",
                                  "include/linux/tcp.*",
                                  "include/uapi/linux/tcp.*",
                                  "net/ipv4/tcp.*",
                                  "net/ipv6/tcp.*"
                              ]}),
                         trees=data.Target.ANY,
                         arches={"x86_64"},
                         sets={"net"},
                         components=data.Target.NONE,
                         sources=data.Target.ALL)
