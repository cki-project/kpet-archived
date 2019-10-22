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
                                    kpet_with_db, COMMONTREE_XML,
                                    INDEX_BASE_YAML, create_asset_files,
                                    SUITE_BASE)


class IntegrationMiscTests(IntegrationTests):
    """Miscellaneous integration tests"""

    def test_empty_tree_list(self):
        """Test tree listing with empty database"""
        assets = {
            "index.yaml": """
                # Empty but valid database
                {}
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_with_db, assets_path, "tree", "list")

    def test_empty_run_generate(self):
        """Test run generation with empty database"""
        assets = {
            "index.yaml": """
                # Empty but valid database
                {}
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            status=1,
            stderr_matching=r'.*Tree "tree" not found.*')

    def test_minimal_run_generate(self):
        """Test run generation with empty database"""
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

                # Minimal, but fully-functional database
                arches:
                    - arch
                trees:
                    tree:
                        template: tree.xml
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_run_generate, assets_path,
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_missing_tree_template_run_generate(self):
        """Test run generation with a missing tree template"""
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
                    missing_template:
                        template: missing_template.xml
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_run_generate,
                                assets_path,
                                "-t", "missing_template",
                                status=1,
                                stderr_matching=r'.*TemplateNotFound.*')

    def test_missing_suite_file_run_generate(self):
        """Test run generation with a missing suite file"""
        assets = {
            "index.yaml": INDEX_BASE_YAML + """
                trees:
                    tree:
                        template: tree.xml
                suites:
                    - missing.yaml
            """,
            "tree.xml": """
                <job/>
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_run_generate,
                                assets_path,
                                status=1,
                                stderr_matching=r'.*missing.yaml.*')

    def test_invalid_top_yaml_tree_list(self):
        """Test tree listing with invalid YAML in the top database file"""
        assets = {
            "index.yaml": INDEX_BASE_YAML + """
                tree: {
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_with_db, assets_path,
                                "--debug", "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_suite_yaml_tree_list(self):
        """Test tree listing with invalid YAML in a suite file"""
        assets = {
            "index.yaml": INDEX_BASE_YAML + """
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                {
                maintainers:
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_with_db, assets_path,
                                "--debug", "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_top_data_tree_list(self):
        """Test tree listing with invalid data in the top database file"""
        assets = {
            "index.yaml": INDEX_BASE_YAML + """
                trees: {}
                unknown_node: True
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_with_db, assets_path,
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Base data.*')

    def test_invalid_suite_data_tree_list(self):
        """Test tree listing with invalid data in a suite file"""
        assets = {
            "index.yaml": INDEX_BASE_YAML + """
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: "Suite data with missing nodes"
                location: somewhere
                maintainers:
                  - maint1
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_with_db, assets_path,
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Suite data.*')

    def test_empty_suite_run_generate(self):
        """Test run generation with an empty suite"""
        assets = {
            "index.yaml": """
                host_types:
                    normal: {}
                host_type_regex: ^normal
                recipesets:
                    rcs1:
                      - normal
                arches:
                    - arch
                trees:
                    tree:
                        template: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: Empty suite
                location: somewhere
                maintainers:
                  - maint1
                cases: []

            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(kpet_run_generate, assets_path,
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_empty_case_no_patterns_run_generate(self):
        """Test run generation with an empty test case without patterns"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": """
                description: suite1
                location: somewhere
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_empty_case_with_a_pattern_run_generate(self):
        """Test run generation with an empty test case with a pattern"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": """
                description: suite1
                location: somewhere
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_preparation_tasks_are_added(self):
        """Test source-matching with a specific case"""
        assets = {
            "index.yaml": """
                host_type_regex: ^normal
                host_types:
                    normal:
                        tasks: tasks.xml
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
            """,
            "suite1.yaml": SUITE_BASE.format(1) + """
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": COMMONTREE_XML,
            "tasks.xml": "<task>Some preparation task</task>"
        }

        assets_path = create_asset_files(self.test_dir, assets)

        # Only non-specific case matches baseline
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<task>\s*Some preparation task\s*</task>.*')

    def test_suites_expose_their_name(self):
        """Test suites' "name" field should be exposed to Beaker templates"""
        assets = {
            "index.yaml": INDEX_BASE_YAML,
            "suite.yaml": """
                name: first_suite_with_name
                description: suite1
                location: somewhere
                cases:
                    - name: case1
                      max_duration_seconds: 600
            """,
            "tree.xml": """
            <job>
              {% for recipeset in RECIPESETS %}
                {% for HOST in recipeset %}
                  {% for suite in HOST.suites %}
                    {{ suite.name }}
                  {% endfor %}
                {% endfor %}
              {% endfor %}
            </job>
            """,
        }

        assets_path = create_asset_files(self.test_dir, assets)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            stdout_matching=r'.*<job>\s*first_suite_with_name\s*</job>.*')
