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

import jinja2
from lxml import etree
from kpet import data


class Test:
    # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """A test run - an execution of a particular case of a test suite"""

    def __init__(self, suite, case):
        """
        Initialize a test run.

        Args:
            suite:  The test suite (kpet.data.Suite) being executed.
            case:   The test case of the test suite (kpet.data.Case) being
                    executed.
        """
        assert isinstance(suite, data.Suite)
        assert isinstance(case, data.Case)
        assert case in suite.cases

        # pylint: disable=invalid-name
        self.name = " - ".join(filter(lambda x: x is not None,
                                      (suite.name, case.name)))
        self.universal_id = \
            case.universal_id if case.universal_id is not None else \
            suite.universal_id if suite.universal_id is not None else \
            None
        self.origin = suite.origin
        self.location = suite.location
        self.max_duration_seconds = case.max_duration_seconds
        self.waived = \
            case.waived if case.waived is not None else \
            suite.waived if suite.waived is not None else \
            False
        self.role = case.role
        self.environment = case.environment
        self.maintainers = suite.maintainers + case.maintainers


class Host:
    # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """A host running tests"""

    # pylint: disable=redefined-builtin
    def __init__(self, name, type, suites_and_cases):
        """
        Initialize a host run.

        Args:
            name:               Name of the host.
            type:               Type of the host.
            suites_and_cases:   A list of suite-and-cases tuples.
                                The first element of each tuple being a
                                kpet.data.Suite instance and the second
                                element - a list of kpet.data.Case instances.
                                Represents the suites and their cases to be
                                executed on the host.
        """
        assert isinstance(type, data.HostType)
        assert isinstance(suites_and_cases, list)
        assert all((isinstance(suite_and_cases, tuple) and
                    isinstance(suite_and_cases[0], data.Suite) and
                    isinstance(suite_and_cases[1], list) and
                    suite_and_cases[1] and
                    all(isinstance(case, data.Case)
                        for case in suite_and_cases[1]))
                   for suite_and_cases in suites_and_cases)

        self.name = name
        self.hostname = type.hostname
        self.ignore_panic = type.ignore_panic
        # pylint: disable=invalid-name
        # TODO: Remove once database transitions to *_list fields
        self.hostRequires = type.hostRequires
        self.partitions = type.partitions
        self.kickstart = type.kickstart
        self.tasks = type.tasks

        # Collect host parameters and create "suite" and "test" lists
        self.tests = list()
        hostRequires_list = [type.hostRequires]
        partitions_list = [type.partitions]
        kickstart_list = [type.kickstart]
        for suite, cases in suites_and_cases:
            hostRequires_list.append(suite.hostRequires)
            partitions_list.append(suite.partitions)
            kickstart_list.append(suite.kickstart)
            for case in cases:
                hostRequires_list.append(case.hostRequires)
                partitions_list.append(case.partitions)
                kickstart_list.append(case.kickstart)
                self.tests.append(Test(suite, case))

        # Remove undefined template paths
        self.hostRequires_list = filter(lambda e: e is not None,
                                        hostRequires_list)
        self.partitions_list = filter(lambda e: e is not None,
                                      partitions_list)
        self.kickstart_list = filter(lambda e: e is not None,
                                     kickstart_list)

        # Put waived tests at the end
        self.tests.sort(key=lambda t: t.waived)


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
            contain hosts with tests to be executed on them.
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
            A list of Host instances with suite and test runs assigned to them
        """
        host_types = \
            database.host_types \
            if database.host_types is not None \
            else {"": data.DEFAULT_HOST_TYPE}

        hosts = []
        for host_type_name, host_type in host_types.items():
            # Create a host suite-and-cases list
            host_suites = []
            for pool_suite in pool_suites.copy():
                suite, pool_cases = pool_suite
                # Create case list from suite cases matching the host type
                host_suite_cases = []
                for case in pool_cases.copy():
                    host_type_regex = \
                        case.host_type_regex or \
                        suite.host_type_regex or \
                        database.host_type_regex
                    if database.host_types is None or \
                       host_type_regex and \
                       host_type_regex.fullmatch(host_type_name):
                        host_suite_cases.append(case)
                        pool_cases.remove(case)
                # Add suite and cases to the host list if there are any cases
                if host_suite_cases:
                    host_suites.append((suite, host_suite_cases))
                # Remove suite from the pool, if it has no more cases
                if not pool_cases:
                    pool_suites.remove(pool_suite)
            # Add host to list, if it has suites to run
            if host_suites:
                hosts.append(Host(host_type_name, host_type, host_suites))

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
            A list of Host instances with test runs assigned to them
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
