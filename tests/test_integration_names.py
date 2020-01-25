# Copyright (c) 2020 Red Hat, Inc. All rights reserved. This copyrighted
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
"""Integration tests for test name handling"""
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    create_asset_files)

DATABASE_WITH_1_SUITE_YAML = """
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
"""

DATABASE_WITH_2_SUITES_YAML = \
    DATABASE_WITH_1_SUITE_YAML + """
        - suite2.yaml
"""

SUITE_1_WITH_ONE_CASE_YAML = """
    location: somewhere
    maintainers: ["maint1"]
    cases:
          max_duration_seconds: 100
"""

SUITE_2_WITH_ONE_CASE_YAML = """
    location: somewhere
    maintainers: ["maint1"]
    cases:
          max_duration_seconds: 100
"""

SUITE_1_WITH_TWO_DIFFERENT_CASES = """
    location: somewhere
    maintainers: ["maint1"]
    cases:
        - name: case1
          max_duration_seconds: 100
    cases:
        - name: case2
          max_duration_seconds: 200
"""

SUITE_2_WITH_TWO_DIFFERENT_CASES = """
    name: suite2
    location: somewhere
    maintainers: ["maint1"]
    cases:
        - name: case1
          max_duration_seconds: 100
    cases:
        - name: case2
          max_duration_seconds: 200
"""

SUITE_1_WITH_TWO_SAME_CASES = """
    name: suite1
    location: somewhere
    maintainers: ["maint1"]
    cases:
        - name: case1
          max_duration_seconds: 100
        - name: case1
          max_duration_seconds: 200
"""


class IntegrationNamesTests(IntegrationTests):
    """Integration tests for test name handling"""

    def test_suite_ids(self):
        """Test repeated and non-repeated test names work correctly"""

        # Single empty test name
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Double empty test name from cases
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*Repeated test names encountered: \{\(\)\}.*")

        # Double empty test name from suites
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "suite2.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*Repeated test names encountered: \{\(\)\}.*")

        # Double non-empty test name from cases
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case
                      max_duration_seconds: 100
                    - name: case
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*encountered: \{\('case',\)\}.*")

        # Double non-empty test name from suite
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                name: suite
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*encountered: \{\('suite',\)\}.*")

        # Double non-empty test name from two suites' cases
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case
                      max_duration_seconds: 100
            """,
            "suite2.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*encountered: \{\('case',\)\}.*")

        # Double non-empty test name from two suites' names
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                name: suite
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "suite2.yaml": """
                name: suite
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*encountered: \{\('suite',\)\}.*")

        # Double assymetric-placement test name
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                name: foo
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "suite2.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: foo
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r".*encountered: \{\('foo',\)\}.*")

        # Single empty test name
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Single non-empty case name
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Single non-empty suite and case name
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                name: suite
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Unique case names
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_1_SUITE_YAML,
            "suite1.yaml": """
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case1
                      max_duration_seconds: 100
                    - name: case2
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Unique suite names
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                name: suite1
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "suite2.yaml": """
                name: suite2
                location: somewhere
                maintainers: [""]
                cases:
                    - max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')

        # Unique suite and case names
        assets_path = create_asset_files(self.test_dir, {
            "index.yaml": DATABASE_WITH_2_SUITES_YAML,
            "suite1.yaml": """
                name: suite1
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case1
                      max_duration_seconds: 100
            """,
            "suite2.yaml": """
                name: suite2
                location: somewhere
                maintainers: [""]
                cases:
                    - name: case2
                      max_duration_seconds: 100
            """,
            "tree.txt.j2": ""
        })
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'^$')
