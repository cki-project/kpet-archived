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
from .test_integration import (IntegrationTests, kpet_run_generate,
                               COMMONTREE_XML, create_asset_files)


class IntegrationMatchLocationTypesTests(IntegrationTests):
    """Integration tests expecting a match in location_types"""

    def test_match_location_types_no_patterns(self):
        """Test location-type matching a case with no patterns"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: case1
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: []
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Doesn't match a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Doesn't match an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_location_types_one_pattern(self):
        """Test location-type matching cases with one pattern"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: tarball-path
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: tarball-path
                    - name: rpm-path
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: rpm-path
                    - name: repo-path
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: repo-path
                    - name: tarball-url
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: tarball-url
                    - name: rpm-url
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: rpm-url
                    - name: repo-url
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or: repo-url
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Only one case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-path\s*</job>.*')
        # Only one case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'tarball-url\s*</job>.*')
        # Only one case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-path\s*</job>.*')
        # Only one case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm-url\s*</job>.*')
        # Only one case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-path\s*</job>.*')
        # Only one case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo-url\s*</job>.*')

    def test_match_location_types_two_patterns(self):
        """Test location-type matching cases with two patterns"""
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
                    tree: tree.xml
                suites:
                    - suite.yaml
            """,
            "suite.yaml": """
                description: suite1
                maintainers:
                  - maint1
                cases:
                    - name: tarball
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - tarball-path
                            - tarball-url
                    - name: rpm
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - rpm-path
                            - rpm-url
                    - name: repo
                      max_duration_seconds: 600
                      pattern:
                        location_types:
                          or:
                            - repo-path
                            - repo-url
            """,
            "tree.xml": COMMONTREE_XML,
        }

        assets_path = create_asset_files(self, assets)

        # Tarball case matches a tarball path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # Tarball case matches a tarball URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.tar.gz",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*tarball\s*</job>.*')
        # RPM case matches an RPM path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # RPM case matches an RPM URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/kernel.rpm",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*rpm\s*</job>.*')
        # Repo case matches a repo path
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
        # Repo case matches a repo URL
        self.assertKpetProduces(
            kpet_run_generate, assets_path,
            "-k", "http://example.com/repo",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*repo\s*</job>.*')
