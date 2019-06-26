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
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    COMMONTREE_XML, create_asset_files,
                                    SUITE_BASE)

INDEX_BASE = """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                    panicky:
                        ignore_panic: true
                    multihost_1: {}
                recipesets:
                    rcs1:
                      - normal
                      - panicky
                    rcs2:
                      - multihost_1
                      - multihost_2

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    normal: {}
"""


class IntegrationMultihostTypesTests(IntegrationTests):
    """Multihost integration tests with at least one type"""

    def test_multihost_one_type_no_regex_no_suites(self):
        """Test multihost support with one type, but no regex/suites"""
        assets = {
            "index.yaml": INDEX_BASE,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSrcMatchesNoneOfTwoSuites(
            assets_path)

    def test_multihost_one_type_no_regex_two_suites(self):
        """Test multihost support with one type, no regex, and two suites"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal

                recipesets:
                    rcs1:
                      - other

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    normal: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSrcMatchesNoneOfTwoSuites(
            assets_path)

    def test_multihost_one_type_db_regex(self):
        """Test multihost support with one type and DB-level regex"""
        assets = {
            "index.yaml": INDEX_BASE + """
                host_type_regex: normal
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSrcMatchesTwoSuites(assets_path)

    def test_multihost_one_type_suite_regex(self):
        """Test multihost support with one type and suite-level regexes"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    normal: {}
                    not_normal: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": """
                description: suite1
                maintainers:
                  - maint1
                host_type_regex: normal
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
                host_type_regex: not_normal
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

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSrcMatchesOneOfTwoSuites(
            assets_path)

    def test_multihost_one_type_case_regex(self):
        """Test multihost support with one type and case-level regexes"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    normal: {}
                    not_normal: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      host_type_regex: normal
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      host_type_regex: not_normal
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSrcMatchesOneOfTwoSuites(
            assets_path)

    def test_multihost_two_types_one_case_each(self):
        """Test multihost support with two types matching one case each"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                    panicky:
                        ignore_panic: true
                    multihost_1: {}
                recipesets:
                    rcs1:
                      - a
                      - b

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    a: {}
                    b: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      host_type_regex: a
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      host_type_regex: b
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'HOST\s*suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_first(self):
        """
        Test multihost support with two types and both cases matching the
        first one.
        """
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                recipesets:
                    rcs1:
                      - a
                      - b

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    a: {}
                    b: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      host_type_regex: a
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      host_type_regex: a
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_second(self):
        """
        Test multihost support with two types and both cases matching the
        second one.
        """
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                recipesets:
                    rcs1:
                      - a
                      - b

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    a: {}
                    b: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      host_type_regex: b
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      host_type_regex: b
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_both(self):
        """
        Test multihost support with two types and both cases matching both
        types.
        """
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal: {}
                    panicky:
                        ignore_panic: true
                    multihost_1: {}
                recipesets:
                    rcs1:
                      - a
                      - b

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_types:
                    a: {}
                    b: {}
                suites:
                    - suite1.yaml
                    - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
                      host_type_regex: ".*"
                      pattern:
                        sources:
                          or:
                            - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                    - name: case2
                      max_duration_seconds: 600
                      host_type_regex: ".*"
                      pattern:
                        sources:
                          or:
                            - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_one_type_suite_wrong_regex(self):
        """Test multihost schema invalid error with wrong suite regexes"""
        assets = {
            "index.yaml": """
            host_type_regex: ^normal
            recipesets:
                rcs1:
                  - normal
            arches:
                - arch
            trees:
                tree: tree.xml
            host_types:
                normal: {}
            suites:
                - suite1.yaml
                - suite2.yaml
            """,
            "suite1.yaml": """
            description: suite1
            maintainers:
              - maint1
            host_type_regex: normal
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
            host_type_regex: not_normal
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

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSchemaInvalidError(
            assets_path,
            "One of host_type_regex")

    def test_multihost_one_type_case_wrong_regex(self):
        """Test multihost schema invalid error with wrong case regexes"""
        assets = {
            "index.yaml": """
            host_type_regex: ^normal
            recipesets:
                rcs1:
                  - normal
            arches:
                - arch
            trees:
                tree: tree.xml
            host_types:
                normal: {}
            suites:
                - suite1.yaml
                - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                - name: case1
                  max_duration_seconds: 600
                  host_type_regex: normal
                  pattern:
                    sources:
                      or:
                        - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                - name: case2
                  max_duration_seconds: 600
                  host_type_regex: not_normal
                  pattern:
                    sources:
                      or:
                        - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)
        self.assertKpetSchemaInvalidError(
            assets_path,
            "One of host_type_regex")

    def test_multihost_one_type_wrong_regex(self):
        """Test multihost schema invalid error with wrong db-level regex"""

        assets = {
            "index.yaml": """
            host_type_regex: ^normal
            recipesets:
                rcs1:
                  - normal
            arches:
                - arch
            trees:
                tree: tree.xml
            host_types:
                normal: {}
            host_type_regex: not_normal
            suites:
                - suite1.yaml
                - suite2.yaml
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                - name: case1
                  max_duration_seconds: 600
                  pattern:
                    sources:
                      or:
                        - a
            """,
            "suite2.yaml": SUITE_BASE.format(2) + """
                - name: case2
                  max_duration_seconds: 600
                  pattern:
                    sources:
                      or:
                        - d
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetSchemaInvalidError(
            assets_path,
            "One of host_type_regex")
