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
                               get_patch_path, COMMONTREE_XML,
                               create_asset_files)


class IntegrationMatchTests(IntegrationTests):
    """Integration tests expecting a match"""

    def test_match_sources_one_case_no_patterns(self):
        """Test source-matching a case with no patterns"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
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

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": """
                description: suite2
                maintainers:
                  - maint1
                cases:
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": """
                description: suite1
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
                          or:
                            - a
            """,
            "suite2.yaml": """
                description: suite2
                maintainers:
                  - maint1
                cases:
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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
                    tree: tree.xml
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          not:
                              sources: null
                          sources: a
            """,
            "suite2.yaml": """
                description: suite2
                maintainers:
                  - maint1
                cases:
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

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

    def test_match_arches_no_patterns(self):
        """Test architecture-matching a case with no patterns"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - ""
                    - arch
                trees:
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          arches:
                            or: []
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Doesn't match a non-empty (default "arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_arches_one_pattern(self):
        """Test architecture-matching a case with one pattern"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - ""
                    - arch
                    - not_arch
                trees:
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          arches: arch
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-a", "not_arch",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_arches_two_patterns(self):
        """Test architecture-matching a case with two patterns"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - ""
                    - arch
                    - not_arch
                    - other_arch
                trees:
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        arches:
                          or:
                            - arch
                            - other_arch
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches non-default (but listed) architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-a", "other_arch",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-a", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-a", "not_arch",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_no_patterns(self):
        """Test tree-matching a case with no patterns"""
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
                    "": .xml
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        trees:
                          or: []
            """,
            "tree.xml": COMMONTREE_XML,
            ".xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Doesn't match a non-empty (default "tree") tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_one_pattern(self):
        """Test tree-matching a case with one pattern"""
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
                    "": .xml
                    tree: tree.xml
                    not_tree: not_tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          trees: tree
            """,
            "tree.xml": COMMONTREE_XML,
            "not_tree.xml": COMMONTREE_XML,
            ".xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "not_tree",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_trees_two_patterns(self):
        """Test tree-matching a case with two patterns"""
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
                    "": .xml
                    tree: tree.xml
                    not_tree: not_tree.xml
                    other_tree: other_tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        trees:
                          or:
                            - tree
                            - other_tree
            """,
            "tree.xml": COMMONTREE_XML,
            "not_tree.xml": COMMONTREE_XML,
            ".xml": COMMONTREE_XML,
            "other_tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches non-default (but listed) tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-t", "other_tree",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "not_tree",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_location_types_no_patterns(self):
        """Test location-type matching a case with no patterns"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: []
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Doesn't match a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_location_types_one_pattern(self):
        """Test location-type matching cases with one pattern"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: tarball-path
                      max_duration_seconds: 600
                      pattern:
                          location_types: tarball-path
                    - name: rpm-path
                      max_duration_seconds: 600
                      pattern:
                          location_types: rpm-path
                    - name: repo-path
                      max_duration_seconds: 600
                      pattern:
                          location_types: repo-path
                    - name: tarball-url
                      max_duration_seconds: 600
                      pattern:
                          location_types: tarball-url
                    - name: rpm-url
                      max_duration_seconds: 600
                      pattern:
                          location_types: rpm-url
                    - name: repo-url
                      max_duration_seconds: 600
                      pattern:
                          location_types: repo-url
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Only one case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-path\s*</job>.*')
        # Only one case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-url\s*</job>.*')
        # Only one case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-path\s*</job>.*')
        # Only one case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-url\s*</job>.*')
        # Only one case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-path\s*</job>.*')
        # Only one case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-url\s*</job>.*')

    def test_match_location_types_two_patterns(self):
        """Test location-type matching cases with two patterns"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: tarball
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - tarball-path
                            - tarball-url
                    - name: rpm
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - rpm-path
                            - rpm-url
                    - name: repo
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - repo-path
                            - repo-url
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Tarball case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # Tarball case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # RPM case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # RPM case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # Repo case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
        # Repo case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
