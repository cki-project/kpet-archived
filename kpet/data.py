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
from kpet.schema import Invalid, Int, Struct, StrictStruct, Ancestry, \
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
                    version=String(),
                    patterns=List(StrictStruct(pattern=Regex(),
                                               case_name=String())),
                    cases=List(Class(Case))
                ),
                optional=dict(
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

    def match_case_set(self, src_path_set):
        """
        Return test cases responsible for testing any files in a set.

        Args:
            src_path_set:   A set of source file paths to match cases against,
                            or an empty set for all source files.

        Returns:
            A set of test cases responsible for testing at least some of the
            specified files.
        """
        if src_path_set:
            case_set = set()
            for pattern in self.patterns:
                for src_path in src_path_set:
                    if pattern['pattern'].match(src_path):
                        case = self.get_case(pattern['case_name'])
                        if case:
                            case_set.add(case)
        else:
            case_set = set(self.cases)
        return case_set

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
        return bool(self.match_case_set(src_path_set))


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

        def convert(old_data):
            """Convert the data from old to new format"""
            data = old_data.copy()
            data['suites'] = list(data['suites'].values())
            return data

        super().__init__(
            ScopedYAMLFile(
                Ancestry(
                    StrictStruct(
                        schema=StrictStruct(version=Int()),
                        suites=Dict(YAMLFile(Class(Suite))),
                        trees=Dict(String())
                    ),
                    convert,
                    StrictStruct(
                        schema=StrictStruct(version=Int()),
                        suites=List(YAMLFile(Class(Suite))),
                        trees=Dict(String())
                    )
                )
            ),
            dir_path + "/index.yaml"
        )

        self.dir_path = dir_path

    def match_suite_set(self, src_path_set):
        """
        Return test suites responsible for testing any files in a set.

        Args:
            src_path_set:   A set of source file paths to match suites
                            against, or an empty set for all files.

        Returns:
            A set of test suites responsible for testing at least some of the
            specified files.
        """
        return {suite for suite in self.suites
                if suite.matches(src_path_set)}

    def match_case_set(self, src_path_set):
        """
        Return test cases responsible for testing any files in a set.

        Args:
            src_path_set:   A set of source file paths to match cases against,
                            or an empty set for all source files.

        Returns:
            A set of test cases responsible for testing at least some of the
            specified files.
        """
        case_set = set()
        for suite in self.suites:
            case_set |= suite.match_case_set(src_path_set)
        return case_set
