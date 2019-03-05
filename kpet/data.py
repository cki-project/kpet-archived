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
"""KPET data"""

import os
from kpet.schema import Invalid, Struct, StrictStruct, \
    List, Dict, String, Regex, ScopedYAMLFile, YAMLFile, Class, Boolean

# pylint: disable=raising-format-tuple


class Object:   # pylint: disable=too-few-public-methods
    """An abstract data object"""
    def __init__(self, schema, data):
        """
        Initialize an abstract data object with a schema validating and
        resolving a supplied data.

        Args:
            schema: The schema of the data, must recognize to a Struct.
            data:   The object data to be validated against and resolved with
                    the schema.
        """
        # Validate and resolve the data
        try:
            data = schema.resolve(data)
        except Invalid:
            raise Invalid("Invalid {} data", type(self).__name__)

        # Recognize the schema
        schema = schema.recognize()
        assert isinstance(schema, Struct)
        try:
            schema.validate(data)
        except Invalid as exc:
            raise Exception("Resolved data is invalid:\n{}".format(exc))

        # Assign members
        for member_name in schema.required.keys():
            setattr(self, member_name, data[member_name])
        for member_name in schema.optional.keys():
            setattr(self, member_name, data.get(member_name, None))


class Case(Object):     # pylint: disable=too-few-public-methods
    """Test case"""
    def __init__(self, data):
        super().__init__(
            Struct(
                required=dict(
                    name=String(),
                ),
                optional=dict(
                    host_type_regex=Regex(),
                    ignore_panic=Boolean(),
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String(),
                    tasks=String(),
                )
            ),
            data
        )


class Suite(Object):    # pylint: disable=too-few-public-methods
    """Test suite"""
    def __init__(self, data):
        super().__init__(
            Struct(
                required=dict(
                    description=String(),
                    patterns=List(StrictStruct(pattern=Regex(),
                                               case_name=String())),
                    cases=List(Class(Case))
                ),
                optional=dict(
                    host_type_regex=Regex(),
                    tasks=String(),
                    ignore_panic=Boolean(),
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String()
                )
            ),
            data
        )

    def get_case(self, name):
        """
        Get a test case by name.

        Args:
            name:   Name of the test case to get.

        Returns:
            The matching test case, or None if not found.
        """
        for case in self.cases:
            if case.name == name:
                return case
        return None

    def match_case_list(self, src_path_set):
        """
        Return a list of test cases responsible for testing any files in a
        set.

        Args:
            src_path_set:   A set of source file paths to match cases against,
                            or an empty set for all source files.

        Returns:
            A list of test cases responsible for testing at least some of the
            specified files.
        """
        if src_path_set:
            case_list = list()
            for pattern in self.patterns:
                for src_path in src_path_set:
                    if pattern['pattern'].match(src_path):
                        case = self.get_case(pattern['case_name'])
                        if case and case not in case_list:
                            case_list.append(case)
        else:
            case_list = self.cases.copy()
        return case_list

    def matches(self, src_path_set):
        """
        Check if the suite is responsible for testing any files in a set.

        Args:
            src_path_set:   A set of source file paths to check against,
                            or an empty set for all files.

        Returns:
            True if the suite is responsible for testing at least some of
            the specified files.
        """
        return bool(self.match_case_list(src_path_set))


class HostType(Object):     # pylint: disable=too-few-public-methods
    """Host type"""

    def __init__(self, data):
        """
        Initialize a host type.
        """
        super().__init__(
            Struct(optional=dict(
                ignore_panic=Boolean(),
                hostRequires=String(),
                partitions=String(),
                kickstart=String(),
                tasks=String(),
            )),
            data
        )


# Host type to use when there are none defined
DEFAULT_HOST_TYPE = HostType({})


class Base(Object):     # pylint: disable=too-few-public-methods
    """Database"""

    @staticmethod
    def is_dir_valid(dir_path):
        """
        Check if a directory is a valid database.

        Args:
            dir_path:   Path to the directory to check.

        Returns:
            True if the directory is a valid database directory,
            False otherwise.
        """
        return os.path.isfile(dir_path + "/index.yaml")

    def __init__(self, dir_path):
        """
        Initialize a database object.
        """
        assert self.is_dir_valid(dir_path)

        super().__init__(
            ScopedYAMLFile(
                Struct(
                    required=dict(
                        suites=List(YAMLFile(Class(Suite))),
                        trees=Dict(String()),
                    ),
                    optional=dict(
                        host_types=Dict(Class(HostType)),
                        host_type_regex=Regex()
                    )
                )
            ),
            dir_path + "/index.yaml"
        )

        self.dir_path = dir_path

    def match_suite_list(self, src_path_set):
        """
        Return a list of test suites responsible for testing any files in a
        set.

        Args:
            src_path_set:   A set of source file paths to match suites
                            against, or an empty set for all files.

        Returns:
            A list of test suites responsible for testing at least some of the
            specified files.
        """
        return [suite for suite in self.suites if suite.matches(src_path_set)]

    def match_case_list(self, src_path_set):
        """
        Return a list of test cases responsible for testing any files in a
        set.

        Args:
            src_path_set:   A set of source file paths to match cases against,
                            or an empty set for all source files.

        Returns:
            A list of test cases responsible for testing at least some of the
            specified files.
        """
        case_list = list()
        for suite in self.suites:
            case_list += suite.match_case_list(src_path_set)
        return case_list
