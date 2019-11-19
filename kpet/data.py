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
from functools import reduce
from kpet.schema import Invalid, Struct, Choice, \
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
            raise Invalid("Invalid {} data".format(type(self).__name__))

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
    """
    Execution target which suite/case patterns match against.

    A target has a fixed collection of parameters, each of which can be
    assigned a target set.

    A target set is either:

        - a set of strings,
        - Target.ALL, meaning a set containing all possible strings, or
        - Target.ANY, meaning any possible set of strings.
    """

    # Empty target set
    NONE = set()
    # Complete target set
    ALL = ()
    # Any target set
    ANY = None

    @staticmethod
    def set_is_valid(target_set):
        """
        Check if a target set is valid.

        Args:
            target_set: The target set to check.

        Returns:
            True if the target set is valid, false otherwise.
        """
        return target_set == Target.ANY or \
            target_set == Target.ALL or \
            (isinstance(target_set, set) and
             all(isinstance(x, str) for x in target_set))

    def __init__(self, trees=None, arches=None, components=None, sources=None):
        """
        Initialize a target.

        Args:
            trees:          A target set of names of the kernel trees we're
                            executing against.
            arches:         A target set of names of the architectures we're
                            executing on.
            components:     A target set of names of extra components included
                            into the tested kernel build.
            sources:        A target set of paths to the source files to cover
                            with tests.
        """
        assert Target.set_is_valid(trees)
        assert Target.set_is_valid(arches)
        assert Target.set_is_valid(components)
        assert Target.set_is_valid(sources)

        self.trees = trees
        self.arches = arches
        self.components = components
        self.sources = sources


class Pattern(Object):  # pylint: disable=too-few-public-methods
    """Execution target pattern"""

    # Target field qualifiers
    qualifiers = {"trees", "arches", "components", "sources"}

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
            True if the node matched, False if not,
            and None if the result could be any.
        """
        assert isinstance(target, Target)
        assert qualifier is None or qualifier in self.qualifiers

        def sub_op(result_x, result_y):
            """Combine two sub-results using the specified operation"""
            if result_x is None:
                return result_y
            if result_y is None:
                return result_x
            return result_x and result_y if and_op else result_x or result_y

        if isinstance(node, dict):
            sub_results = []
            for name, sub_node in node.items():
                assert qualifier is None or name not in self.qualifiers, \
                       "Qualifier is already specified"
                sub_result = self.__node_matches(
                    target, (name != "or"), sub_node,
                    name if name in self.qualifiers else qualifier)
                if sub_result is not None and name == "not":
                    sub_result = not sub_result
                sub_results.append(sub_result)
            result = reduce(sub_op, sub_results) if sub_results else and_op
        elif isinstance(node, list):
            sub_results = [
                self.__node_matches(target, True, sub_node, qualifier)
                for sub_node in node
            ]
            result = reduce(sub_op, sub_results) if sub_results else and_op
        elif isinstance(node, RE):
            assert qualifier is not None, "Qualifier not specified"
            param = getattr(target, qualifier)
            if param == Target.ALL:
                result = True
            elif param == Target.ANY:
                result = None
            else:
                for value in param:
                    if node.fullmatch(value):
                        result = True
                        break
                else:
                    result = False
        elif node is None:
            assert qualifier is not None, "Qualifier not specified"
            param = getattr(target, qualifier)
            if param == Target.ANY:
                result = None
            else:
                result = (param == Target.ALL)
        else:
            assert False, "Unknown node type: " + type(node).__name__

        return result

    def matches(self, target):
        """
        Check if the pattern matches a target.

        Args:
            target: The target (an instance of Target) to match.

        Returns:
            True if the pattern matches the target, False if not.
        """
        assert isinstance(target, Target)
        node_matches = self.__node_matches(target, True, self.data, None)
        return node_matches is None or node_matches


class Case(Object):     # pylint: disable=too-few-public-methods
    """Test case"""

    def __init__(self, data):
        sets_schema = Reduction(Regex(), lambda x: [x], List(Regex()))
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
                    sets=sets_schema,
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
        sets_schema = Reduction(Regex(), lambda x: [x], List(Regex()))

        super().__init__(
            Struct(
                required=dict(
                    description=String(),
                    location=String(),
                    cases=List(Class(Case))
                ),
                optional=dict(
                    host_type_regex=Regex(),
                    hostRequires=String(),
                    partitions=String(),
                    kickstart=String(),
                    pattern=Class(Pattern),
                    sets=sets_schema,
                    origin=String(),
                    url_suffix=String(),
                    maintainers=List(String(), min_len=1)
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

    def validate_host_type_regex(self):
        """
        Check if any of the regexes are invalid.
        Raises:
            schema.Invalid when finding an invalid regex
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
                    raise Invalid(error.format("host_type_regex", "host_types",
                                               suite.description, case.name,
                                               host_type_regex.pattern,
                                               host_types))

    def validate_suite_origins(self):
        """
        Check that suite origins are valid.
        Raises:
            schema.Invalid when finding an invalid origin.
        """
        for suite in self.suites:
            if self.origins is None:
                if suite.origin is not None:
                    raise Invalid(
                        f'Suite "{suite.description}" has origin specified, '
                        f'but available origins are not defined in '
                        f'the database.'
                    )
            else:
                if suite.origin is None:
                    raise Invalid(
                        f'Suite "{suite.description}" has no origin specified'
                    )
                if suite.origin not in self.origins:
                    raise Invalid(
                        f'Suite "{suite.description}" has unknown origin '
                        f'specified: "{suite.origin}".\n'
                        f'Expecting one of the following: '
                        f'{", ".join(self.origins.keys())}.'
                    )

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
                    raise Invalid(error.format(arch_regex.pattern,
                                               self.arches))
                tree_arches |= regex_arches

            self.trees[name]["arches"] = list(tree_arches)

    def convert_sets(self):
        """
        Convert each suite / cases sets from a list of regexes
        to a list of set names matching those regexes

        Raises:
            A schema.Invalid exception when finding an invalid regex
        """

        def get_sets_from_regex_list(regex_list):
            """
            Generate a set of set names matching any regular expressions from
            the supplied list. Return None if None is passed instead,
            signifying a missing set and regular expression list respectively.

            Args:
                regex_list:     The list of regular expressions to match
                                against. None if regex_list is missing.

            Returns:
                A set of set names matched by the list of regular
                expressions, or None, signifying a missing set, in case the
                list was missing.

            Raises:
                Invalid - if a regular expression didn't match any set names.
            """
            if regex_list is None:
                return None
            sets = set()
            for regex in regex_list:
                match = set(filter(regex.fullmatch, self.sets.keys()))
                if match == set():
                    raise Invalid(f'Regex "{regex.pattern}" matches no sets')
                sets |= match
            return sets

        for suite in self.suites:
            suite.sets = get_sets_from_regex_list(suite.sets)

            if suite.sets is None:
                suite.sets = set()

            for case in suite.cases:
                case.sets = get_sets_from_regex_list(case.sets)

                if case.sets is None:
                    case.sets = suite.sets

                if not case.sets <= suite.sets:
                    raise Invalid("Case sets are not a subset of suite sets "
                                  "in suite: {}\ncase: {}".
                                  format(suite.description, case.name))

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
                        recipesets=Dict(List(String())),
                        variables=Dict(
                            Struct(required=dict(description=String()),
                                   optional=dict(default=String()))
                        ),
                        origins=Dict(String()),
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
        if self.variables is None:
            self.variables = dict()
        # Validate suite origins
        self.validate_suite_origins()
        # Regex check
        self.validate_host_type_regex()
        # Replace the list of regexes with a list of available arches
        # for easier usage
        self.convert_tree_arches()
        # Replace the list of regexes in each suite / case
        # with a list of matching sets
        self.convert_sets()
