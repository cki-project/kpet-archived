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


class Suite:
    # pylint: disable=too-few-public-methods,too-many-instance-attributes
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
        self.hostRequires = suite.hostRequires  # pylint: disable=invalid-name
        self.partitions = suite.partitions
        self.kickstart = suite.kickstart
        self.cases = cases
        self.maintainers = suite.maintainers
        self.url_suffix = suite.url_suffix


class Host:
    # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """A host running test suites"""

    # pylint: disable=redefined-builtin
    def __init__(self, name, type, suites):
        """
        Initialize a host run.

        Args:
            name:       Name of the host.
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
        self.suites = suites

        self.name = name
        self.hostname = type.hostname


class Base:     # pylint: disable=too-few-public-methods
    """A specific execution of tests in a database"""

    @staticmethod
    def __get_recipesets(database, target, sets):
        """
        Distribute hosts, suites and cases to recipesets.

        Args:
            database:   The database to get test data from.
            target:     The target (a data.Target) to match/run tests against.
                        The target's tree must be present in the database.
            sets:       A set of names of test sets to have their members
                        included into the run. None if all suites and cases
                        should be included, regardless if members or not.

        Returns:
            A list of recipesets - host synchronization domains - lists which
            contain hosts with suites and their cases to be executed on them.
        """
        assert isinstance(database, data.Base)
        assert isinstance(target, data.Target)
        assert sets is None or isinstance(sets, set)

        # get hosts and their testcases
        hosts = Base.__get_hosts(database, target, sets)

        # load recipesets assignments from yaml
        db_recipesets = database.recipesets

        # Distribute hosts to their respective recipesets
        recipesets_of_hosts = list()
        for host_recipeset_names in db_recipesets.values():
            recipeset = list()
            for host_recipeset_name in host_recipeset_names:
                for host in hosts:
                    if host.name == host_recipeset_name:
                        recipeset.append(host)

            if recipeset:
                recipesets_of_hosts.append(recipeset)

        return recipesets_of_hosts

    @staticmethod
    def __distribute_into_hosts(database, pool_suites):
        """
        Distribute suites and their cases to hosts

        Args:
            database:       The database to get host_types from.
            pool_suites:    A list of tuples, each containing a suite
                            and its cases selected for the run.
        Returns:
            A list of Host instances with suite runs assigned to them
        """
        host_types = \
            database.host_types \
            if database.host_types is not None \
            else {"": data.DEFAULT_HOST_TYPE}

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
                       host_type_regex.fullmatch(host_type_name):
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
                suites = list(sorted(suites, key=lambda suite:
                                     len([case for case in suite.cases if
                                          case.waived])))
                hosts.append(Host(host_type_name, host_type, suites))

        return hosts

    @staticmethod
    def __get_hosts(database, target, sets):
        """
        Get a list of hosts to run.

        Args:
            database:   The database to get test data from.
            target:     The target (a data.Target) to match/run tests against.
            sets:       A set of names of test sets to have their members
                        included into the run. None if all suites and cases
                        should be included, regardless if members or not.
        Returns:
            A list of Host instances with suite runs assigned to them
        """
        assert isinstance(database, data.Base)
        assert isinstance(target, data.Target)
        assert sets is None or isinstance(sets, set)

        # Build a pool of suites and cases
        pool_suites = []
        for suite in database.suites:
            if suite.matches(target) and \
               (sets is None or suite.sets & sets):
                pool_cases = []
                for case in suite.cases:
                    if case.matches(target) and \
                       (sets is None or case.sets & sets):
                        pool_cases.append(case)
                if pool_cases:
                    pool_suites.append((suite, pool_cases))

        return Base.__distribute_into_hosts(database, pool_suites)

    def __init__(self, database, target, sets):
        """
        Initialize a test run.

        Args:
            database:   The database to get test data from.
            target:     The target (a data.Target) to match/run tests against.
                        The target's tree must be present in the database.
            sets:       A set of names of test sets to have their members
                        included into the run. None if all suites and cases
                        should be included, regardless if members or not.
        """
        assert isinstance(database, data.Base)
        assert isinstance(target, data.Target)
        assert sets is None or isinstance(sets, set)
        assert target.trees is None or \
            target.trees <= set(database.trees.keys())
        assert target.arches is None or \
            target.arches <= set(database.arches)

        self.database = database
        self.target = target
        self.recipesets_of_hosts = self.__get_recipesets(database, target,
                                                         sets)

    # pylint: disable=too-many-arguments
    def generate(self, description, kernel_location, lint, variables):
        """
        Generate Beaker XML which would execute tests in the database.
        The target supplied at creation must have exactly one tree and exactly
        one architecture for this to succeed.

        Args:
            description:        The run description string.
            kernel_location:    Kernel location string (a tarball or RPM URL).
            lint:               Lint and reformat the XML output, if True.
            variables:          A dictionary of extra template variables.
        Returns:
            The beaker XML string.
        """
        assert isinstance(description, str)
        assert isinstance(kernel_location, str)
        assert isinstance(lint, bool)
        assert isinstance(variables, dict)
        assert self.target.trees is not None and len(self.target.trees) == 1
        assert self.target.arches is not None and len(self.target.arches) == 1

        tree_name = list(self.target.trees)[0]
        arch_name = list(self.target.arches)[0]

        params = dict(
            DESCRIPTION=description,
            KURL=kernel_location,
            ARCH=arch_name,
            TREE=tree_name,
            RECIPESETS=self.recipesets_of_hosts,
            VARIABLES=variables,
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
            undefined=jinja2.StrictUndefined,
        )
        template = jinja_env.get_template(
                        self.database.trees[tree_name]['template'])
        text = template.render(params)

        if lint:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.XML(text.encode("utf-8"), parser)
            text = etree.tostring(tree, encoding="utf-8",
                                  xml_declaration=True,
                                  pretty_print=True).decode("utf-8")
        return text
