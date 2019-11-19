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
"""Template variable integration tests"""
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    create_asset_files)


# DB index.yaml with a required template variable "x"
DB_YAML_REQUIRED_VARIABLE_X = """
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
    variables:
        x:
            description: Variable x
"""

# DB index.yaml with an optional template variable "x"
DB_YAML_OPTIONAL_VARIABLE_X = \
    DB_YAML_REQUIRED_VARIABLE_X + """
            default: DEFAULT
"""

# An empty suite's YAML file
SUITE_YAML_EMPTY = """
    description: Empty suite
    location: somewhere
    maintainers:
      - maint1
    cases: []

"""

# Database outputting a required template variable "x"
DB_REQUIRED_VARIABLE_X = {
    "index.yaml": DB_YAML_REQUIRED_VARIABLE_X,
    "suite.yaml": SUITE_YAML_EMPTY,
    "tree.xml": "{{ VARIABLES.x }}"
}

# Database outputting an optional template variable "x"
DB_OPTIONAL_VARIABLE_X = {
    "index.yaml": DB_YAML_OPTIONAL_VARIABLE_X,
    "suite.yaml": SUITE_YAML_EMPTY,
    "tree.xml": "{{ VARIABLES.x }}"
}


class IntegrationVariablesTests(IntegrationTests):
    """Integration tests for template variable interface"""

    def test_short_opt(self):
        """Check short option is accepted"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_REQUIRED_VARIABLE_X)

        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "-v", "x=VALUE", "--no-lint",
                                stdout_matching=r'VALUE')

    def test_long_opt(self):
        """Check long option is accepted"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_REQUIRED_VARIABLE_X)

        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "--variable", "x=VALUE", "--no-lint",
                                stdout_matching=r'VALUE')

    def test_required_not_specified(self):
        """Check not specifying a required variable aborts rendering"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_REQUIRED_VARIABLE_X)

        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r'.*Required variables not set: x\..*')

    def test_unknown_specified(self):
        """Check specifying an unknown variable aborts rendering"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_REQUIRED_VARIABLE_X)

        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "--no-lint", "-v", "y=VALUE", status=1,
            stderr_matching=r'.*Unknown variables specified: y\..*')

    def test_optional_not_specified(self):
        """Check not specifying an optional variable outputs defaults"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_OPTIONAL_VARIABLE_X)

        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint",
            stdout_matching=r'DEFAULT')

    def test_optional_specified(self):
        """Check specifying an optional variable overrides default"""
        assets_path = create_asset_files(self.test_dir,
                                         DB_OPTIONAL_VARIABLE_X)

        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "-v", "x=VALUE", "--no-lint",
                                stdout_matching=r'VALUE')
