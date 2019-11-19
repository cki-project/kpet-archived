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
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    get_patch_path, COMMONTREE_XML,
                                    create_asset_files, INDEX_BASE_YAML,
                                    SUITE_BASE)


class IntegrationMatchSuitesCasesTests(IntegrationTests):
    """Integration tests expecting a match in suites or cases"""

    def test_match_sources_one_case_no_patterns(self):
        """Test source-matching a case with no patterns"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_match_sources_one_case_one_pattern(self):
        """Test source-matching a case with one pattern"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: a
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches patches it should
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_one_case_two_patterns(self):
        """Test source-matching a case with two patterns"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches first patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches second patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches both patches only once
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_cases(self):
        """Test source-matching two cases"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: a
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_suites(self):
        """Test source-matching two suites"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree:
                        template: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_suite(self):
        """Test source-matching with a specific suite"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree:
                        template: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": """
                description: suite1
                location: somewhere
                maintainers:
                  - maint1
                pattern:
                  not:
                    sources: null
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Only non-specific suite matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All suites can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_case(self):
        """Test source-matching with a specific case"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree:
                        template: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        not:
                          sources: null
                        sources: a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or: d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Only non-specific case matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All cases can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')
