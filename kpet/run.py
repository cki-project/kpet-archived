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
"""Execution of tests from the database"""

import os
import jinja2
from lxml import etree
from kpet import data


class Base:     # pylint: disable=too-few-public-methods
    """A specific execution of tests in a database"""

    def __init__(self, database, src_path_set):
        """
        Initialize a test run.

        Args:
            database:           The database to get test data from.
            src_path_set:       A set of paths to source files the executed
                                tests should cover, empty set for all files.
                                Affects the selection of test suites and test
                                cases to run.
        """
        assert isinstance(database, data.Base)
        self.database = database
        self.src_path_set = src_path_set

    # pylint: disable=too-many-arguments
    def generate(self, description, tree_name, arch_name,
                 kernel_location, lint):
        """
        Generate Beaker XML which would execute tests in the database.

        Args:
            description:        The run description string.
            tree_name:          Name of the kernel tree to run against.
            arch_name:          The name of the architecture to run on.
            kernel_location:    Kernel location string (a tarball or RPM URL).
            lint:               Lint and reformat the XML output, if True.
        Returns:
            The beaker XML string.
        """
        assert isinstance(description, str)
        assert isinstance(tree_name, str)
        assert tree_name in self.database.trees
        assert isinstance(arch_name, str)
        assert isinstance(kernel_location, str)

        params = dict(
            DESCRIPTION=description,
            KURL=kernel_location,
            ARCH=arch_name,
            TREE=tree_name,
            SRC_PATH_SET=self.src_path_set,
            SUITE_SET=set(self.database.suites),
            match_suite_set=self.database.match_suite_set,
            match_case_set=self.database.match_case_set,
            getenv=os.getenv,
        )

        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader([self.database.dir_path]),
            trim_blocks=True,
            keep_trailing_newline=True,
            lstrip_blocks=True,
            autoescape=jinja2.select_autoescape(
                enabled_extensions=('xml'),
                default_for_string=True,
            ),
        )
        template = jinja_env.get_template(self.database.trees[tree_name])
        text = template.render(params)

        if lint:
            parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8")
            tree = etree.XML(text, parser)
            text = etree.tostring(tree, encoding="utf-8",
                                  xml_declaration=True,
                                  pretty_print=True).decode("utf-8")
        return text
