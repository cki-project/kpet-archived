# Copyright (c) 2019 Red Hat, Inc. All rights reserved. This copyrighted
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
"""Integration multihost tests"""
from .test_integration import IntegrationTests, kpet_run_generate


class IntegrationMultihostTests(IntegrationTests):
    """Multihost integration tests"""

    def test_multihost_no_types_no_regex_no_suites(self):
        """Test multihost support without types/regex/suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/no_types/no_regex/no_suites")

    def test_multihost_no_types_no_regex_two_suites(self):
        """Test multihost support without types/regex and two suites"""
        self.assertKpetSrcMatchesTwoSuites(
            "multihost/no_types/no_regex/two_suites")

    def test_multihost_no_types_wildcard_regex_two_suites(self):
        """
        Test multihost support without types, with a DB-level wildcard regex,
        and two suites.
        """
        self.assertKpetSrcMatchesTwoSuites("multihost/no_types/db_regex")

    def test_multihost_one_type_no_regex_no_suites(self):
        """Test multihost support with one type, but no regex/suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/one_type/no_regex/no_suites")

    def test_multihost_one_type_no_regex_two_suites(self):
        """Test multihost support with one type, no regex, and two suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/one_type/no_regex/two_suites")

    def test_multihost_one_type_db_regex(self):
        """Test multihost support with one type and DB-level regex"""
        self.assertKpetSrcMatchesTwoSuites("multihost/one_type/db_regex")

    def test_multihost_one_type_suite_regex(self):
        """Test multihost support with one type and suite-level regexes"""
        self.assertKpetSrcMatchesOneOfTwoSuites(
            "multihost/one_type/suite_regex")

    def test_multihost_one_type_case_regex(self):
        """Test multihost support with one type and case-level regexes"""
        self.assertKpetSrcMatchesOneOfTwoSuites(
            "multihost/one_type/case_regex")

    def test_multihost_two_types_one_case_each(self):
        """Test multihost support with two types matching one case each"""
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/one_case_each",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'HOST\s*suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_first(self):
        """
        Test multihost support with two types and both cases matching the
        first one.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_first",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_second(self):
        """
        Test multihost support with two types and both cases matching the
        second one.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_second",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_both(self):
        """
        Test multihost support with two types and both cases matching both
        types.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_both",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
