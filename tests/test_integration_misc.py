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
from .test_integration import (IntegrationTests, kpet_run_generate,
                               kpet_with_db)


class IntegrationMiscTests(IntegrationTests):
    """Integration tests expecting empty results or errors"""

    def test_empty_tree_list(self):
        """Test tree listing with empty database"""
        self.assertKpetProduces(kpet_with_db, "empty/db", "tree", "list")

    def test_empty_run_generate(self):
        """Test run generation with empty database"""
        self.assertKpetProduces(
            kpet_run_generate, "empty/db",
            status=1,
            stderr_matching=r'.*Architecture "arch" not found.*')

    def test_minimal_run_generate(self):
        """Test run generation with empty database"""
        self.assertKpetProduces(kpet_run_generate, "minimal",
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_missing_tree_template_run_generate(self):
        """Test run generation with a missing tree template"""
        self.assertKpetProduces(kpet_run_generate,
                                "invalid/semantics/missing_tree_template",
                                "-t", "missing_template",
                                status=1,
                                stderr_matching=r'.*TemplateNotFound.*')

    def test_missing_suite_file_run_generate(self):
        """Test run generation with a missing suite file"""
        self.assertKpetProduces(kpet_run_generate,
                                "invalid/semantics/missing_suite_file",
                                status=1,
                                stderr_matching=r'.*missing.yaml.*')

    def test_invalid_top_yaml_tree_list(self):
        """Test tree listing with invalid YAML in the top database file"""
        self.assertKpetProduces(kpet_with_db, "invalid/yaml/top",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_suite_yaml_tree_list(self):
        """Test tree listing with invalid YAML in a suite file"""
        self.assertKpetProduces(kpet_with_db, "invalid/yaml/suite",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_top_data_tree_list(self):
        """Test tree listing with invalid data in the top database file"""
        self.assertKpetProduces(kpet_with_db, "invalid/data/top",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Base data.*')

    def test_invalid_suite_data_tree_list(self):
        """Test tree listing with invalid data in a suite file"""
        self.assertKpetProduces(kpet_with_db, "invalid/data/suite",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Suite data.*')

    def test_empty_suite_run_generate(self):
        """Test run generation with an empty suite"""
        self.assertKpetProduces(kpet_run_generate, "empty/suite",
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_empty_case_no_patterns_run_generate(self):
        """Test run generation with an empty test case without patterns"""
        self.assertKpetProduces(
            kpet_run_generate, "empty/case_no_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_empty_case_with_a_pattern_run_generate(self):
        """Test run generation with an empty test case with a pattern"""
        self.assertKpetProduces(
            kpet_run_generate, "empty/case_with_a_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
