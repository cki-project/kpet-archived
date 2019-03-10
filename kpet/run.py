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


class Suite:    # pylint: disable=too-few-public-methods
    """A test suite run"""

    def __init__(self, suite, cases):
        """
        Initialize a test suite run.

        Args:
            suite:          The suite to run.
            cases:          List of the suite's cases to run.
        """
        assert isinstance(suite, data.Suite)
        assert isinstance(cases, list)
        for case in cases:
            assert case in suite.cases

        self.description = suite.description
        self.tasks = suite.tasks
        self.ignore_panic = suite.ignore_panic
        self.hostRequires = suite.hostRequires  # pylint: disable=invalid-name
        self.partitions = suite.partitions
        self.kickstart = suite.kickstart
        self.cases = cases


class Host:     # pylint: disable=too-few-public-methods
    """A host running test suites"""

    # pylint: disable=redefined-builtin
    def __init__(self, type, suites):
        """
        Initialize a host run.

        Args:
            type:       Type of the host.
            suites:     List of suite runs to execute.
        """
        assert isinstance(type, data.HostType)
        assert isinstance(suites, list)
        for suite in suites:
            assert isinstance(suite, Suite)

        self.ignore_panic = type.ignore_panic
        # pylint: disable=invalid-name
        self.hostRequires = type.hostRequires
        self.partitions = type.partitions
        self.kickstart = type.kickstart
        self.tasks = type.tasks
        self.suites = suites


class Base:     # pylint: disable=too-few-public-methods
    """A specific execution of tests in a database"""

    @staticmethod
    def __get_hosts(database, src_path_set):
        """
        Get a list of hosts to run.

        Args:
            database:           The database to get test data from.
            src_path_set:       A set of paths to source files the executed
                                tests should cover, empty set for all files.
                                Affects the selection of test suites and test
                                cases to run.
        """
        assert isinstance(database, data.Base)
        host_types = \
            database.host_types \
            if database.host_types is not None \
            else {"": data.DEFAULT_HOST_TYPE}

        # Build a pool of suites and cases
        pool_suites = [
            (suite,
             suite.match_case_list(database.specific, src_path_set))
            for suite
            in database.match_suite_list(src_path_set)
        ]

        # Distribute suites and their cases to hosts
        hosts = list()
        for host_type_name, host_type in host_types.items():
            # Create a suite run list
            suites = list()
            for pool_suite in pool_suites.copy():
                suite, pool_cases = pool_suite
                # Create case list from cases matching host type
                cases = []
                for case in pool_cases.copy():
                    host_type_regex = \
                        case.host_type_regex or \
                        suite.host_type_regex or \
                        database.host_type_regex
                    if database.host_types is None or \
                       host_type_regex and \
                       host_type_regex.match(host_type_name):
                        cases.append(case)
                        pool_cases.remove(case)
                # Add the suite run to the list, if it has cases to run
                if cases:
                    suites.append(Suite(suite, cases))
                # Remove suite from the pool, if it has no more cases
                if not pool_cases:
                    pool_suites.remove(pool_suite)
            # Add host to list, if it has suites to run
            if suites:
                hosts.append(Host(host_type, suites))

        return hosts

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
        self.hosts = self.__get_hosts(database, src_path_set)

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
            HOSTS=self.hosts,
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
