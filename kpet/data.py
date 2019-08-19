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
import re
from kpet.schema import Invalid, Struct, Choice, NonEmptyList, \
    List, Dict, String, Regex, ScopedYAMLFile, YAMLFile, Class, Boolean, \
    Int, Null, RE, Reduction

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


class Target:  # pylint: disable=too-few-public-methods, too-many-arguments
    """Execution target that suite/case patterns match against"""
    def __init__(self, trees=None, arches=None, components=None, sets=None,
                 sources=None):
        """
        Initialize a target.

        Args:
            trees:          The name of the kernel tree we're executing
                            against, or a set thereof.
                            None (the default) means all the trees.
            arches:         The name of the architecture we're executing on or
                            a set thereof.
                            None (the default) means all the architectures.
            components:     The name of an extra component included into the
                            tested kernel build, or a set thereof.
                            None (the default) means all the extra components.
            sets:           The name of the set of tests to restrict the run
                            to, or a set thereof. None (the default) means all
                            the sets (i.e. no restriction).
            sources:        The path to the source file we're covering, or a
                            set thereof. None (the default) means all the
                            files.
        """
        def normalize(arg):
            if arg is None or isinstance(arg, set):
                return arg
            return {arg}

        self.trees = normalize(trees)
        self.arches = normalize(arches)
        self.components = normalize(components)
        self.sets = normalize(sets)
        self.sources = normalize(sources)


class Pattern(Object):  # pylint: disable=too-few-public-methods
    """Execution target pattern"""

    # Target field qualifiers
    qualifiers = {"trees", "arches", "components", "sets", "sources"}

    """An execution target pattern"""
    def __init__(self, data):
        """
        Initialize an execution pattern.

        Args:
            data:       Pattern data.
        """
        class NonRecursiveChoice(Choice):
            """Choice schema preventing recursive recognition"""
            def __init__(self, *args):
                super().__init__(*args)
                self.recognizing = False

            def recognize(self):
                if self.recognizing:
                    recognized = self
                else:
                    self.recognizing = True
                    recognized = super().recognize()
                    self.recognizing = False
                return recognized

        class OpsOrValues(NonRecursiveChoice):
            """Pattern operations or values"""
            def __init__(self):
                super().__init__(
                    Null(),
                    Regex(),
                    List(self),
                    Struct(optional={k: self for k in {"not", "and", "or"}})
                )

        ops_or_values_schema = OpsOrValues()

        class OpsOrQualifiers(NonRecursiveChoice):
            """Pattern operations or qualifiers"""
            def __init__(self):
                fields = {}
                fields.update({k: self for k in {"not", "and", "or"}})
                fields.update({k: ops_or_values_schema
                               for k in Pattern.qualifiers})
                super().__init__(
                    List(self),
                    Struct(optional=fields)
                )

        try:
            self.data = OpsOrQualifiers().resolve(data)
        except Invalid:
            raise Invalid("Invalid pattern")

    # Documentation overhead for multiple functions would be too big, and
    # spread-out logic too hard to grasp.
    # pylint: disable=too-many-branches
    def __node_matches(self, target, and_op, node, qualifier):
        """
        Check if a pattern node matches a target.

        Args:
            target:     The target (an instance of Target) to match.
            and_op:     True if the node items should be "and'ed" together,
                        False if "or'ed".
            node:       The pattern node matching against the target.
                        Either None, a regex, a dictionary or a list.
            qualifier:  Qualifier (name of the target parameter being
                        matched), if already encountered, None if not.
                        Cannot be None if node is a None or a regex.

        Returns:
            True if the node matched, False otherwise.
        """
        assert isinstance(target, Target)
        assert qualifier is None or qualifier in self.qualifiers

        if isinstance(node, dict):
            result = and_op
            for name, sub_node in node.items():
                assert qualifier is None or name not in self.qualifiers, \
                       "Qualifier is already specified"
                sub_result = self.__node_matches(
                    target, (name != "or"), sub_node,
                    name if name in self.qualifiers else qualifier)
                if name == "not":
                    sub_result = not sub_result
                if and_op:
                    result &= sub_result
                else:
                    result |= sub_result
        elif isinstance(node, list):
            result = and_op
            for sub_node in node:
                sub_result = self.__node_matches(
                    target, True, sub_node, qualifier)
                if and_op:
                    result &= sub_result
                else:
                    result |= sub_result
        elif isinstance(node, RE):
            assert qualifier is not None, "Qualifier not specified"
            value_set_or_none = getattr(target, qualifier)
            if value_set_or_none is None:
                result = True
            else:
                for value in value_set_or_none:
                    if node.fullmatch(value):
                        result = True
                        break
                else:
                    result = False
        elif node is None:
            assert qualifier is not None, "Qualifier not specified"
            result = getattr(target, qualifier) is None
        else:
            assert False, "Unknown node type: " + type(node).__name__

        return result

    def matches(self, target):
        """
        Check if the pattern matches a target.

        Args:
            target: The target (an instance of Target) to match.

        Returns:
            True if the pattern matches the target, False otherwise.
        """
        assert isinstance(target, Target)
        return self.__node_matches(target, True, self.data, None)


class Case(Object):     # pylint: disable=too-few-public-methods
    """Test case"""

    def __init__(self, data):
        super().__init__(
            Struct(
                required=dict(
                    name=String(),
                    max_duration_seconds=Int(),
                ),
                optional=dict(
                    host_type_regex=Regex(),
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String(),
                    pattern=Class(Pattern),
                    waived=Boolean(),
                    role=String(),
                    url_suffix=String(),
                    environment=Dict(String()),
                )
            ),
            data
        )
        if self.pattern is None:
            self.pattern = Pattern({})
        if self.environment is None:
            self.environment = {}
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
        return self.pattern.matches(target)


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
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String(),
                    pattern=Class(Pattern),
                    url_suffix=String(),
                    maintainers=NonEmptyList(String())
                )
            ),
            data
        )
        if self.pattern is None:
            self.pattern = Pattern({})

    def matches(self, target):
        """
        Check if the suite matches a target.

        Args:
            target: The target to match against.

        Returns:
            True if the suite matches the target, False otherwise.
        """
        return self.pattern.matches(target)


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
                hostname=String(),
                partitions=String(),
                kickstart=String(),
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

    def validate_host_type_regex(self):
        """
        Check if any of the regexes are invalid.
        Returns:
            Raises a schema.Invalid exception when finding an invalid regex
        """
        host_types = list((self.host_types or {}).keys())

        error = ("One of {0} regexes\n" +
                 "doesn't match any of the available {1}\n" +
                 "In suite: {2}\n" +
                 "In case: {3}\n" +
                 "The regex: {4}\n" +
                 "The avaliable {1}: {5}")

        for suite in self.suites or []:
            for case in suite.cases or []:
                host_type_regex = case.host_type_regex or \
                        suite.host_type_regex or \
                        self.host_type_regex

                for host in host_types:
                    if host_type_regex.fullmatch(host):
                        break
                else:
                    raise Invalid(error, "host_type_regex", "host_types",
                                  suite.description, case.name,
                                  host_type_regex.pattern,
                                  host_types)

    def convert_tree_arches(self):
        """
        Convert each tree's supported architecture specification from
        a list of regexes to a list of architecture names matching those
        regexes

        Returns:
            Raises a schema.Invalid exception when finding an invalid regex
        """

        wildcard = [re.compile(".*")]

        for name, value in self.trees.items():
            tree_arches = set()
            for arch_regex in value.get("arches", wildcard):
                regex_arches = set(filter(arch_regex.fullmatch, self.arches))
                if regex_arches == set():
                    error = ("One of 'trees: arches:' regexes\n" +
                             "doesn't match any of the available arches\n" +
                             "The regex: '{0}'\n" +
                             "The avaliable arches: {1}")
                    raise Invalid(error, arch_regex.pattern,
                                  self.arches)
                tree_arches |= regex_arches

            self.trees[name]["arches"] = list(tree_arches)

    def __init__(self, dir_path):
        """
        Initialize a database object.
        """
        assert self.is_dir_valid(dir_path)

        arches_schema = Reduction(Regex(), lambda x: [x], List(Regex()))

        super().__init__(
            ScopedYAMLFile(
                Struct(
                    required=dict(
                    ),
                    optional=dict(
                        suites=List(YAMLFile(Class(Suite))),
                        trees=Dict(
                            Struct(required=dict(template=String()),
                                   optional=dict(arches=arches_schema))
                        ),
                        arches=List(String()),
                        components=Dict(String()),
                        sets=Dict(String()),
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
        if self.components is None:
            self.components = {}
        if self.sets is None:
            self.sets = {}
        if self.suites is None:
            self.suites = []
        # Regex check
        self.validate_host_type_regex()
        # Replace the list of regexes with a list of available arches
        # for easier usage
        self.convert_tree_arches()
