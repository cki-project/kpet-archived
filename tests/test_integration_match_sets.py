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
                                    COMMONTREE_XML, create_asset_files)


class IntegrationMatchSetsTests(IntegrationTests):
    """Integration tests expecting a match in suites or cases"""

    def test_match_one_suite(self):
        """Test set matching by matching a single suite and all its cases"""
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                  cases:
                    - name: case1
                      max_duration_seconds: 600
            """,
            "suite2.yaml": """
                  description: suite2
                  location: somewhere
                  maintainers:
                    - maint2
                  sets:
                    - bar
                  cases:
                    - name: case2
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "foo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches a different suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "bar",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # Doesn't match any suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "baz",
            stdout_matching=r'.*<job>\s</job>.*')

    def test_match_one_case(self):
        """Test set matching by matching a single case"""
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                    - bar
                  cases:
                    - name: case1
                      max_duration_seconds: 600
                      sets: foo
            """,
            "suite2.yaml": """
                  description: suite2
                  location: somewhere
                  maintainers:
                    - maint2
                  sets:
                    - foo
                    - bar
                  cases:
                    - name: case2
                      max_duration_seconds: 600
                      sets:
                        - bar
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "foo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches a different suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "bar",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')

    def test_match_not_subset_error(self):
        """
        Check for the 'not a subset error'
        by having the a case with sets that it's suite doesn't have
        """
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                    - bar
                  cases:
                    - name: case1
                      max_duration_seconds: 600
                      sets:
                        - foo
                        - baz
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "foo", status=1,
            stderr_matching=r'.*kpet.schema.Invalid: Case sets are not a '
                            r'subset of suite sets in suite:\s*'
                            r'suite1\s*case: case1\b.*')

    def test_match_nonexistent_set_case_error(self):
        """
        Make sure we get an error when specifying an unknown set in case
        """
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                    - bar
                  cases:
                    - name: case1
                      max_duration_seconds: 600
                      sets:
                        - foo
                        - baz
                        - unknown
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "foo", status=1,
            stderr_matching=r'.*kpet.schema.Invalid: .* matches no sets.*')

    def test_match_nonexistent_set_suite_error(self):
        """
        Make sure we get an error when specifying an unknown set in suite
        """
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                    - bar
                    - unknown
                  cases:
                    - name: case1
                      max_duration_seconds: 600
                      sets:
                        - foo
                        - baz
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "foo", status=1,
            stderr_matching=r'.*kpet.schema.Invalid: .* matches no sets.*')

    def test_match_nonexistent_set_error(self):
        """
        Make sure we get an error when specifying
        an unknown set in command line arguments
        """
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
                sets:
                    foo: "Lorem"
                    bar: "ipsum"
                    baz: "dolor"
                """,
            "suite1.yaml": """
                  description: suite1
                  location: somewhere
                  maintainers:
                    - maint1
                  sets:
                    - foo
                  cases:
                    - name: case1
                      max_duration_seconds: 600
                      sets:
                        - foo
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Matches suite
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "-s", "unknown", status=1,
            stderr_matching=r'.*No test sets matched specified regular.*')
