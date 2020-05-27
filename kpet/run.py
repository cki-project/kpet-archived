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

from functools import reduce
import jinja2
from lxml import etree
from kpet import data
from kpet.misc import attr_parentage


class Test:
    # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """A test run - an instance of a test case"""

    def __init__(self, case):
        """
        Initialize a test run as an instance of a test case.

        Args:
            case:           The test case (kpet.data.Case) to instantiate.
        """
        assert isinstance(case, data.Case)

        self.case = case
        self.case_path = ".".join(
            tuple(attr_parentage(case, "id", omit_none=False))[-2::-1]
        )
        self.name = " - ".join(tuple(attr_parentage(case, "name"))[::-1])
        self.universal_id = next(attr_parentage(case, "universal_id"), None)
        self.origin = next(attr_parentage(case, "origin"), None)
        self.location = next(attr_parentage(case, "location"), None)
        self.max_duration_seconds = next(
            attr_parentage(case, "max_duration_seconds"), None
        )
        self.host_type_regex = next(
            attr_parentage(case, "host_type_regex"), None
        )
        self.waived = reduce(max, attr_parentage(case, "waived"), False)
        self.role = next(attr_parentage(case, "role"), None)
        self.environment = reduce(
            lambda x, y: {**y, **x}, attr_parentage(case, "environment"), {}
        )
        self.maintainers = reduce(
            lambda x, y: y + x, attr_parentage(case, "maintainers"), []
        )


class Host:
    # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """A host running tests"""

    def __init__(self, type, tests):
        """
        Initialize a host run.

        Args:
            type:   Type of the host.
            tests:  A list of tests (run.Test instances).
        """
        assert isinstance(type, data.HostType)
        assert isinstance(tests, list)
        assert all(isinstance(test, Test) for test in tests)

        self.hostname = type.hostname
        self.ignore_panic = type.ignore_panic
        self.preboot_tasks = type.preboot_tasks
        self.postboot_tasks = type.postboot_tasks
        # TODO Remove once kpet-db switches to preboot_tasks
        self.tasks = type.preboot_tasks
        self.tests = tests

        # Collect all unique cases referenced by tests,
        # in per-test top-bottom series
        cases = []
        for test in tests:
            pos = len(cases)
            case = test.case
            while case is not None:
                if case not in cases:
                    cases.insert(pos, case)
                case = case.parent

        # Assemble host_requires, partitions and kickstart lists
        # Collect host parameters and create "suite" and "test" lists
        host_requires_list = [type.hostRequires]
        partitions_list = [type.partitions]
        kickstart_list = [type.kickstart]
        for case in cases:
            host_requires_list.append(case.host_requires)
            partitions_list.append(case.partitions)
            kickstart_list.append(case.kickstart)

        # Remove undefined template paths
        self.host_requires_list = filter(lambda e: e is not None,
                                         host_requires_list)
        self.partitions_list = filter(lambda e: e is not None,
                                      partitions_list)
        self.kickstart_list = filter(lambda e: e is not None,
                                     kickstart_list)

        # TODO: For compatibility. Remove when kpet-db is updated.
        # pylint: disable=invalid-name
        self.hostRequires_list = self.host_requires_list

        # Put waived tests at the end
        self.tests.sort(key=lambda t: t.waived)


class Base:     # pylint: disable=too-few-public-methods
    """A specific execution of tests in a database"""

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

        # Distribute tests to host types
        host_type_tests = {}

        def place_case(case):
            # If the case doesn't match the criteria
            if not case.matches(target) or \
               (sets is not None and not case.sets & sets):
                return
            # If this is not a fully-defined case (a non-leaf tree node)
            if case.cases is not None:
                for subcase in case.cases.values():
                    place_case(subcase)
                return
            # Create the test
            test = Test(case)
            # Assign the test to a host type
            for host_type_name in database.host_types:
                if test.host_type_regex and \
                   test.host_type_regex.fullmatch(host_type_name):
                    tests = host_type_tests.get(host_type_name, [])
                    tests.append(test)
                    host_type_tests[host_type_name] = tests
                    break
            else:
                raise Exception(
                    f"No host type found for case {test.case_path}"
                )
        if database.case is not None:
            place_case(database.case)

        # Distribute host types to recipesets
        self.recipesets = []
        for recipeset_host_type_names in database.recipesets.values():
            recipeset = []
            for recipeset_host_type_name in recipeset_host_type_names:
                for host_type_name, tests in host_type_tests.items():
                    if host_type_name == recipeset_host_type_name:
                        recipeset.append(Host(
                            database.host_types[host_type_name],
                            tests
                        ))
                        del host_type_tests[host_type_name]
                        break
            if recipeset:
                self.recipesets.append(recipeset)

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
            RECIPESETS=self.recipesets,
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
