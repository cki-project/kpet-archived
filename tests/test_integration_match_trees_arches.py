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
                                    COMMONTREE_XML, create_asset_files,
                                    SUITE_BASE)


class IntegrationMatchTreesArchesTests(IntegrationTests):
    """Integration tests expecting a match in arches or trees"""

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
                    tree:
                        template: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        arches:
                          or: []
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

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
                    tree:
                        template: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          arches: arch
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
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
                    tree:
                        template: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
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

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches default ("arch") architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
        # Matches non-default (but listed) architecture
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-a", "other_arch",
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
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
                    "":
                        template: .xml
                    tree:
                        template: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        trees:
                          or: []
            """,
            "tree.xml": COMMONTREE_XML,
            ".xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

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
                    "":
                        template: .xml
                    tree:
                        template: tree.xml
                    not_tree:
                        template: not_tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                          trees: tree
            """,
            "tree.xml": COMMONTREE_XML,
            "not_tree.xml": COMMONTREE_XML,
            ".xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
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
                    "":
                        template: .xml
                    tree:
                        template: tree.xml
                    not_tree:
                        template: not_tree.xml
                    other_tree:
                        template: other_tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": SUITE_BASE.format(1) + """
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

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches default ("tree") tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
        # Matches non-default (but listed) tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-t", "other_tree",
            stdout_matching=r'.*<job>\s*HOST\s*suite1 - case1\s*</job>.*')
        # Doesn't match empty tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match another tree
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-t", "not_tree",
            stdout_matching=r'.*<job>\s*</job>.*')
