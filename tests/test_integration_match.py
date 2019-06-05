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
"""Integration tests expecting a match"""
from .test_integration import (IntegrationTests, kpet_run_generate,
                               get_patch_path)


class IntegrationMatchTests(IntegrationTests):
    """Integration tests expecting a match"""

    def test_match_sources_one_case_no_patterns(self):
        """Test source-matching a case with no patterns"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/no_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/no_patterns",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_match_sources_one_case_one_pattern(self):
        """Test source-matching a case with one pattern"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches patches it should
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_one_case_two_patterns(self):
        """Test source-matching a case with two patterns"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches first patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches second patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches both patches only once
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_cases(self):
        """Test source-matching two cases"""
        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_suites(self):
        """Test source-matching two suites"""
        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_suite(self):
        """Test source-matching with a specific suite"""
        # Only non-specific suite matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All suites can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_case(self):
        """Test source-matching with a specific case"""
        # Only non-specific case matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All cases can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_arches_no_patterns(self):
        """Test architecture-matching a case with no patterns"""
        # Doesn't match a non-empty (default "arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/no_patterns",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/no_patterns", "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_arches_one_pattern(self):
        """Test architecture-matching a case with one pattern"""
        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/one_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/one_pattern", "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/one_pattern", "-a", "not_arch",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_arches_two_patterns(self):
        """Test architecture-matching a case with two patterns"""
        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/two_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches non-default (but listed) architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/two_patterns",
            "-a", "other_arch",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/two_patterns", "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another architecture
        self.assertKpetProduces(
            kpet_run_generate, "match/arches/two_patterns", "-a", "not_arch",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_no_patterns(self):
        """Test tree-matching a case with no patterns"""
        # Doesn't match a non-empty (default "tree") tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/no_patterns",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/no_patterns", "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_one_pattern(self):
        """Test tree-matching a case with one pattern"""
        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/one_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/one_pattern", "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/one_pattern", "-t", "not_tree",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_two_patterns(self):
        """Test tree-matching a case with two patterns"""
        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/two_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches non-default (but listed) tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/two_patterns",
            "-t", "other_tree",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/two_patterns", "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another tree
        self.assertKpetProduces(
            kpet_run_generate, "match/trees/two_patterns", "-t", "not_tree",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_location_types_no_patterns(self):
        """Test location-type matching a case with no patterns"""
        # Doesn't match a tarball path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/no_patterns",
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/no_patterns",
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_location_types_one_pattern(self):
        """Test location-type matching cases with one pattern"""
        # Only one case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-path\s*</job>.*')
        # Only one case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-url\s*</job>.*')
        # Only one case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-path\s*</job>.*')
        # Only one case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-url\s*</job>.*')
        # Only one case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-path\s*</job>.*')
        # Only one case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/one_pattern",
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-url\s*</job>.*')

    def test_match_location_types_two_patterns(self):
        """Test location-type matching cases with two patterns"""
        # Tarball case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # Tarball case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # RPM case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # RPM case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # Repo case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
        # Repo case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, "match/location_types/two_patterns",
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
