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
"""Integration miscellaneous tests"""
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    create_asset_files)

INDEX_YAML = """
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
            template: tree.txt.j2
    suites:
        - suite1.yaml
        - suite2.yaml
"""

SUITE_1_WITH_ONE_CASE_YAML = """
    id: suite1
    name: Suite
    location: somewhere
    cases:
        - id: case
          name: Case
          max_duration_seconds: 100
"""

SUITE_2_WITH_ONE_CASE_YAML = """
    id: suite2
    name: Suite
    location: somewhere
    cases:
        - id: case
          name: Case
          max_duration_seconds: 100
"""

SUITE_1_WITH_TWO_DIFFERENT_CASES = """
    id: suite1
    name: Suite
    location: somewhere
    cases:
        - id: case1
          name: Case
          max_duration_seconds: 100
    cases:
        - id: case2
          name: Case
          max_duration_seconds: 200
"""

SUITE_2_WITH_TWO_DIFFERENT_CASES = """
    id: suite2
    name: Suite
    location: somewhere
    cases:
        - id: case1
          name: Case
          max_duration_seconds: 100
    cases:
        - id: case2
          name: Case
          max_duration_seconds: 200
"""

SUITE_1_WITH_TWO_SAME_CASES = """
    id: suite1
    name: Suite
    location: somewhere
    cases:
        - id: case1
          name: Case
          max_duration_seconds: 100
        - id: case1
          name: Case
          max_duration_seconds: 200
"""


class IntegrationIdsTests(IntegrationTests):
    """Integration tests for suite and case ID handling"""

    def test_suite_ids(self):
        """Test suites with repeated and non-repeated IDs work correctly"""
        different_ids_assets_path = create_asset_files(self.test_dir, {
            "index.yaml": INDEX_YAML,
            "suite1.yaml": SUITE_1_WITH_ONE_CASE_YAML,
            "suite2.yaml": SUITE_2_WITH_ONE_CASE_YAML,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, different_ids_assets_path, "--no-lint",
            stdout_matching=r'^$')

        same_ids_assets_path = create_asset_files(self.test_dir, {
            "index.yaml": INDEX_YAML,
            "suite1.yaml": SUITE_1_WITH_ONE_CASE_YAML,
            "suite2.yaml": SUITE_1_WITH_ONE_CASE_YAML,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, same_ids_assets_path, "--no-lint",
            status=1, stderr_matching=r".*repeated suite IDs: \{'suite1'\}.*")

    def test_case_ids(self):
        """Test cases with repeated and non-repeated IDs work correctly"""
        different_ids_assets_path = create_asset_files(self.test_dir, {
            "index.yaml": INDEX_YAML,
            "suite1.yaml": SUITE_1_WITH_TWO_DIFFERENT_CASES,
            "suite2.yaml": SUITE_2_WITH_ONE_CASE_YAML,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, different_ids_assets_path, "--no-lint",
            stdout_matching=r'^$')

        same_ids_assets_path = create_asset_files(self.test_dir, {
            "index.yaml": INDEX_YAML,
            "suite1.yaml": SUITE_1_WITH_TWO_SAME_CASES,
            "suite2.yaml": SUITE_2_WITH_ONE_CASE_YAML,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, same_ids_assets_path, "--no-lint",
            status=1, stderr_matching=r".*repeated case IDs: \{'case1'\}.*")

        two_suites_with_same_case_ids_assets_path = \
            create_asset_files(self.test_dir, {
                "index.yaml": INDEX_YAML,
                "suite1.yaml": SUITE_1_WITH_TWO_DIFFERENT_CASES,
                "suite2.yaml": SUITE_2_WITH_TWO_DIFFERENT_CASES,
                "tree.txt.j2": ""
            })
        self.assertKpetProduces(
            kpet_run_generate, two_suites_with_same_case_ids_assets_path,
            "--no-lint", stdout_matching=r'^$')
