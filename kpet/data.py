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
from kpet.schema import Invalid, Struct, Reduction, NonEmptyList, \
    List, Dict, String, Regex, ScopedYAMLFile, YAMLFile, Class, Boolean

# pylint: disable=raising-format-tuple,access-member-before-definition


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


class Target:  # pylint: disable=too-few-public-methods
    """Execution target that suite/case patterns match against"""
    def __init__(self, trees=None, arches=None, sources=None,
                 location_types=None):
        """
        Initialize a target.

        Args:
            trees:          The name of the kernel tree we're executing
                            against, or a set thereof. An empty set means all
                            the trees.
                            None (the default) is equivalent to an empty set.
            arches:         The name of the architecture we're executing on or
                            a set thereof. An empty set means all the
                            architectures.
                            None (the default) is equivalent to an empty set.
            sources:        The path to the source file we're covering, or a
                            set thereof. An empty set means all the files.
                            None (the default) is equivalent to an empty set.
            location_types: The type of the location of the kernel we're
                            testing (a member of loc.TYPE_SET), or a set
                            thereof. An empty set means all the types.
                            None (the default) is equivalent to an empty set.
        """
        def normalize(arg):
            if arg is None:
                return set()
            if isinstance(arg, set):
                return arg
            return {arg}

        self.trees = normalize(trees)
        self.arches = normalize(arches)
        self.sources = normalize(sources)
        self.location_types = normalize(location_types)


class Pattern(Object):
    """An execution target pattern"""
    def __init__(self, positive, data):
        """
        Initialize an execution pattern.

        Args:
            positive:   True if the pattern is positive, False if negative.
            data:       Pattern data.
        """
        # Accept a list of regexes or a single regex, converted to a
        # single-regex list.
        pattern = Reduction(Regex(), lambda x: [x], List(Regex()))
        super().__init__(
            Struct(
                optional=dict(
                    trees=pattern,
                    arches=pattern,
                    sources=pattern,
                    specific_sources=Boolean(),
                    location_types=pattern,
                )
            ),
            data
        )
        self.positive = positive

    def matches_specific_flag(self, target, name):
        """
        Check if the pattern matches a target for a specific_* flag parameter.

        Args:
            target: The target (an instance of Target) to match.
            name:   The suffix of a specific_* parameter to match.

        Returns:
            True if the pattern matches for the parameter, False otherwise.
        """
        assert isinstance(target, Target)
        assert isinstance(name, str)
        specific = getattr(self, "specific_" + name, None)
        value_set = getattr(target, name)

        # If there's nothing to match
        if specific is None:
            return self.positive
        # Match if wildcard presence matches expectations
        return (value_set != set()) == specific

    def matches_regex_list(self, target, name):
        """
        Check if the pattern matches a target for a regex list parameter.

        Args:
            target: The target (an instance of Target) to match.
            name:   The name of the parameter to match.

        Returns:
            True if the pattern matches for the parameter, False otherwise.
        """
        assert isinstance(target, Target)
        assert isinstance(name, str)
        regex_list = getattr(self, name, None)
        value_set = getattr(target, name)

        # If there's nothing to match
        if regex_list is None or value_set == set():
            return self.positive
        # Match if there are any regex/value matches
        for regex in regex_list:
            for value in value_set:
                if regex.fullmatch(value):
                    return True
        return False

    def matches(self, target):
        """
        Check if the pattern matches a target.

        Args:
            target: The target (an instance of Target) to match.

        Returns:
            True if the pattern matches the target, False otherwise.
        """
        assert isinstance(target, Target)
        for name in target.__dict__.keys():
            if self.matches_specific_flag(target, name) != self.positive or \
               self.matches_regex_list(target, name) != self.positive:
                return False
        return True


class PositivePattern(Pattern):
    """A positive pattern for execution targets"""
    def __init__(self, data):
        super().__init__(True, data)


class NegativePattern(Pattern):
    """A negative pattern for execution targets"""
    def __init__(self, data):
        super().__init__(False, data)


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
                    match=Class(PositivePattern),
                    dont_match=Class(NegativePattern),
                    waived=Boolean(),
                    role=String(),
                    url_suffix=String(),
                    task_params=Dict(String()),
                )
            ),
            data
        )
        if self.match is None:
            self.match = PositivePattern({})
        if self.dont_match is None:
            self.dont_match = NegativePattern({})
        if self.task_params is None:
            self.task_params = {}
        if self.role is None:
            self.role = 'STANDALONE'

    def matches(self, target):
        """
        Check if the case matches a target.

        Args:
            target: The target to match against.

        Returns:
            True if the case matches the target, False otherwise.
        """
        return self.match.matches(target) and self.dont_match.matches(target)


class Suite(Object):    # pylint: disable=too-few-public-methods
    """Test suite"""
    def __init__(self, data):

        super().__init__(
            Struct(
                required=dict(
                    description=String(),
                    cases=List(Class(Case))
                ),
                optional=dict(
                    host_type_regex=Regex(),
                    tasks=String(),
                    ignore_panic=Boolean(),
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String(),
                    match=Class(PositivePattern),
                    dont_match=Class(NegativePattern),
                    url_suffix=String(),
                    maintainers=NonEmptyList(String())
                )
            ),
            data
        )
        if self.match is None:
            self.match = PositivePattern({})
        if self.dont_match is None:
            self.dont_match = NegativePattern({})

    def matches(self, target):
        """
        Check if the suite matches a target.

        Args:
            target: The target to match against.

        Returns:
            True if the suite matches the target, False otherwise.
        """
        return self.match.matches(target) and self.dont_match.matches(target)


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
                    ),
                    optional=dict(
                        suites=List(YAMLFile(Class(Suite))),
                        trees=Dict(String()),
                        arches=List(String()),
                        host_types=Dict(Class(HostType)),
                        host_type_regex=Regex(),
                        recipesets=Dict(List(String()))
                    )
                )
            ),
            dir_path + "/index.yaml"
        )

        self.dir_path = dir_path
        if self.trees is None:
            self.trees = {}
        if self.arches is None:
            self.arches = []
        if self.suites is None:
            self.suites = []
