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
"""Suite origins integration tests"""
from tests.test_integration import (IntegrationTests, kpet_run_generate,
                                    create_asset_files)


# DB index.yaml without origins defined
DB_YAML_WITHOUT_ORIGINS = """
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
"""

# DB index.yaml with two origins ("X" and "Y") defined
DB_YAML_WITH_ORIGINS = \
    DB_YAML_WITHOUT_ORIGINS + """
    origins:
        X: X locations
        Y: Y locations
"""

# A suite YAML without origin specified
SUITE_YAML_WITHOUT_ORIGIN = """
    name: Suite
    location: somewhere
    maintainers:
      - maint1
"""

# A suite YAML with origin "X" specified
SUITE_YAML_WITH_ORIGIN_X = \
    SUITE_YAML_WITHOUT_ORIGIN + """
    origin: X
"""

# A suite YAML with origin "Y" specified
SUITE_YAML_WITH_ORIGIN_Y = \
    SUITE_YAML_WITHOUT_ORIGIN + """
    origin: Y
"""

# A suite YAML with origin "Z" specified
SUITE_YAML_WITH_ORIGIN_Z = \
    SUITE_YAML_WITHOUT_ORIGIN + """
    origin: Z
"""


class IntegrationOriginsTests(IntegrationTests):
    """Integration tests for suite origins"""

    def test_db_without_origins_and_suite_without_origin_works(self):
        """Check no origins at all works"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITHOUT_ORIGINS,
                "suite.yaml": SUITE_YAML_WITHOUT_ORIGIN,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "--no-lint", stdout_matching="")

    def test_db_without_origins_and_suite_with_origin_fails(self):
        """Check using suite origins without origins defined fails"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITHOUT_ORIGINS,
                "suite.yaml": SUITE_YAML_WITH_ORIGIN_X,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r'.* has origin specified\b.*')

    def test_db_with_origins_and_suite_without_origin_fails(self):
        """Check not using suite origins with origins defined fails"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITH_ORIGINS,
                "suite.yaml": SUITE_YAML_WITHOUT_ORIGIN,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r'.* has no origin specified\b.*')

    def test_db_with_origins_and_suite_with_origin_x_works(self):
        """Check using one of two defined origins works"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITH_ORIGINS,
                "suite.yaml": SUITE_YAML_WITH_ORIGIN_X,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "--no-lint", stdout_matching="")

    def test_db_with_origins_and_suite_with_origin_y_works(self):
        """Check using the other one of two defined origins works"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITH_ORIGINS,
                "suite.yaml": SUITE_YAML_WITH_ORIGIN_Y,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(kpet_run_generate, assets_path,
                                "--no-lint", stdout_matching="")

    def test_db_with_origins_and_suite_with_unknown_origin_fails(self):
        """Check using unknown origin fails"""
        assets_path = create_asset_files(
            self.test_dir,
            {
                "index.yaml": DB_YAML_WITH_ORIGINS,
                "suite.yaml": SUITE_YAML_WITH_ORIGIN_Z,
                "tree.xml": ""
            }
        )
        self.assertKpetProduces(
            kpet_run_generate, assets_path, "--no-lint", status=1,
            stderr_matching=r'.* has unknown origin specified: "Z".*')
