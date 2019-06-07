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
from .test_integration import (IntegrationTests, COMMONTREE_XML,
                               create_asset_files)


class IntegrationMultihostNoTypesTests(IntegrationTests):
    """Multihost integration tests with no type"""

    def test_multihost_no_types_no_regex_no_suites(self):
        """Test multihost support without types/regex/suites"""
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
                      - normal
                      - panicky
                    rcs2:
                      - multihost_1
                      - multihost_2

                arches:
                    - arch
                trees:
                    tree: tree.xml
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        self.assertKpetSrcMatchesNoneOfTwoSuites(
            assets_path)

    def test_multihost_no_types_no_regex_two_suites(self):
        """Test multihost support without types/regex and two suites"""
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
                      - normal
                      - panicky
                    rcs2:
                      - multihost_1
                      - multihost_2

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

        self.assertKpetSrcMatchesTwoSuites(
            assets_path)

    def test_multihost_no_types_wildcard_regex_two_suites(self):
        """
        Test multihost support without types, with a DB-level wildcard regex,
        and two suites.
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
                      - normal
                      - panicky
                    rcs2:
                      - multihost_1
                      - multihost_2

                arches:
                    - arch
                trees:
                    tree: tree.xml
                host_type_regex: .*
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

        self.assertKpetSrcMatchesTwoSuites(assets_path)
