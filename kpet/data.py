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
from kpet import misc
from kpet.schema import Invalid, Type, Struct, Choice, \
    List, Dict, String, Regex, ScopedYAMLFile, YAMLFile, Class, Boolean, \
    Int, Null, RE, Reduction, Succession

# pylint: disable=access-member-before-definition, no-member


# Schema for universal IDs
UNIVERSAL_ID_SCHEMA = String(pattern="[.a-zA-Z0-9_-]*")


class Object:   # pylint: disable=too-few-public-methods
    """An abstract data object"""
    def __init__(self, name, schema, data):
        """
        Initialize an abstract data object with a schema validating and
        resolving a supplied data.

        Args:
            name:   Name of the data instance to use in error messages.
            schema: The schema of the data, must recognize to a Struct.
            data:   The object data to be validated against and resolved with
                    the schema.
        """
        # Validate and resolve the data
        try:
            data = schema.resolve(data)
        except Invalid:
            raise Invalid("Invalid {}".format(name))

        # Recognize the schema
        schema = schema.recognize()
        assert isinstance(schema, Struct)
        try:
            schema.validate(data)
        except Invalid as exc:
            raise Exception("Resolved {} is invalid:\n{}".format(name, exc))

        # Assign members
        for member_name in schema.required.keys():
            setattr(self, member_name, data[member_name])
        for member_name in schema.optional.keys():
            setattr(self, member_name, data.get(member_name, None))


class Target:  # pylint: disable=too-few-public-methods, too-many-arguments
    """
    Execution target which case patterns match against.

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
    """Universal test case"""

    def __init__(self, data):
        # TODO Remove once kpet-db transitions to universal cases
        def convert(data):
            """
            Convert either legacy suite data or legacy case data to universal
            case data.

            Args:
                data:   The data to convert.

            Returns:
                The converted data.
            """
            if "hostRequires" in data:
                data["host_requires"] = data.pop("hostRequires")
            if "cases" in data:
                data["cases"] = {
                    str(i): v
                    for i, v in enumerate(data["cases"])
                }
            return data

        sets_schema = Reduction(Regex(), lambda x: [x], List(Regex()))
        super().__init__(
            "test case",
            Reduction(
                # Legacy case
                Struct(
                    required=dict(
                        max_duration_seconds=Int(),
                    ),
                    optional=dict(
                        name=String(),
                        universal_id=UNIVERSAL_ID_SCHEMA,
                        host_type_regex=Regex(),
                        hostRequires=String(),
                        partitions=String(),
                        kickstart=String(),
                        sets=sets_schema,
                        pattern=Class(Pattern),
                        waived=Boolean(),
                        role=String(),
                        environment=Dict(String()),
                        maintainers=List(String()),
                    )
                ),
                convert,
                # Legacy suite
                Struct(
                    required=dict(
                        location=String(),
                        cases=List(Class(Case))
                    ),
                    optional=dict(
                        name=String(),
                        universal_id=UNIVERSAL_ID_SCHEMA,
                        host_type_regex=Regex(),
                        hostRequires=String(),
                        partitions=String(),
                        kickstart=String(),
                        pattern=Class(Pattern),
                        sets=sets_schema,
                        origin=String(),
                        waived=Boolean(),
                        maintainers=List(String())
                    )
                ),
                convert,
                # New case
                Struct(
                    required=dict(),
                    optional=dict(
                        name=String(),
                        universal_id=UNIVERSAL_ID_SCHEMA,
                        origin=String(),
                        location=String(),
                        max_duration_seconds=Int(),
                        host_type_regex=Regex(),
                        host_requires=String(),
                        partitions=String(),
                        kickstart=String(),
                        sets=sets_schema,
                        pattern=Class(Pattern),
                        waived=Boolean(),
                        role=String(),
                        environment=Dict(String()),
                        maintainers=List(String()),
                        cases=Dict(key_schema=String(pattern="[a-zA-Z0-9_-]*"),
                                   value_schema=Choice(YAMLFile(Class(Case)),
                                                       Class(Case),
                                                       # TODO Remove after
                                                       # transition
                                                       Type(Case)))
                    )
                ),
            ),
            data
        )
        if self.pattern is None:
            self.pattern = Pattern({})
        if self.environment is None:
            self.environment = {}
        if self.role is None:
            self.role = 'STANDALONE'
        if self.maintainers is None:
            self.maintainers = []

        self.id = None
        self.parent = None
        if self.cases is not None:
            for id, case in self.cases.items():
                case.id = id
                case.parent = self

    def matches(self, target):
        """
        Check if the case matches a target.

        Args:
            target: The target to match against.

        Returns:
            True if the case matches the target, False otherwise.
        """
        return self.pattern.matches(target)


class HostType(Object):     # pylint: disable=too-few-public-methods
    """Host type"""

    def __init__(self, data):
        """
        Initialize a host type.
        """
        # TODO Drop the old schema once kpet-db is switched to the new one
        def inherit(data):
            if "tasks" in data:
                data["preboot_tasks"] = data.pop("tasks")
            return data
        super().__init__(
            "host type",
            Succession(
                Struct(optional=dict(
                    ignore_panic=Boolean(),
                    hostRequires=String(),
                    hostname=String(),
                    partitions=String(),
                    kickstart=String(),
                    tasks=String(),
                )),
                inherit,
                Struct(optional=dict(
                    ignore_panic=Boolean(),
                    hostRequires=String(),
                    hostname=String(),
                    partitions=String(),
                    kickstart=String(),
                    preboot_tasks=String(),
                    postboot_tasks=String(),
                )),
            ),
            data
        )


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

    # pylint: disable=too-many-branches
    def resolve_case(self, path, case, sets, tests):
        """
        Validate and resolve a case and its sub-cases.

        Args:
            path:   The path of the case being resolved.
            case:   The case to resolve.
            sets:   A set of names of sets the case can belong to.
            tests:  A set of raw test names encountered so far - tuples of
                    names along leaf case branches, top-to-bottom.
                    Will have encountered names added.
        """
        assert isinstance(path, str)
        assert isinstance(case, Case)
        assert isinstance(sets, set)
        assert all(isinstance(set_name, str) for set_name in sets)
        assert isinstance(tests, set)
        assert all(isinstance(test_name, tuple) and
                   all(isinstance(case_name, str) for case_name in test_name)
                   for test_name in tests)

        case_ref = f"case {path}" if path else "the root case"

        # Check host_type_regex matches something
        host_type_names = tuple(self.host_types or {})
        if case.host_type_regex is not None and \
           not any(case.host_type_regex.fullmatch(name)
                   for name in host_type_names):
            raise Invalid(f'Host type regex "{case.host_type_regex.pattern}" '
                          f'of {case_ref} does not match any of the '
                          f'available host type names: {host_type_names}')

        # Check case origin is valid
        if self.origins is None:
            if case.origin is not None:
                raise Invalid(
                    f'{case_ref.capitalize()} has origin specified, '
                    f'but available origins are not defined in '
                    f'the database.'
                )
        else:
            if case.origin is not None and \
               case.origin not in self.origins:
                raise Invalid(
                    f'{case_ref.capitalize()} has unknown origin '
                    f'specified: "{case.origin}".\n'
                    f'Expecting one of the following: '
                    f'{", ".join(self.origins.keys())}.'
                )

        # Resolve set regexes into set names
        if case.sets is None:
            case.sets = sets.copy()
        else:
            resolved_sets = set()
            for regex in case.sets:
                matches = set(filter(regex.fullmatch, sets))
                if not matches:
                    raise Invalid(f"{case_ref.capitalize()} set regex "
                                  f"\"{regex.pattern}\" doesn't match "
                                  f"any of the available sets: {sets}")
                resolved_sets |= matches
            case.sets = resolved_sets

        # If this is a test (a leaf node)
        if case.cases is None:
            # Check the test name is unique
            test_name = tuple(misc.attr_parentage(case, "name"))[::-1]
            if test_name in tests:
                raise Invalid(f"Test for {case_ref} has a non-unique name: "
                              f"{test_name}")
            tests.add(test_name)

            # Check the test has at least one maintainer
            if not reduce(lambda x, y: y + x,
                          misc.attr_parentage(case, "maintainers"), []):
                raise Invalid(f"Test for {case_ref} has no maintainers")

            # Check the test has an origin, if needed
            if self.origins is not None and \
               not list(misc.attr_parentage(case, "origin")):
                raise Invalid(f"Test for {case_ref} has no origin specified")

        # Else this is an intermediate case
        else:
            # Resolve sub-cases
            for subcase in case.cases.values():
                subpath = (path + "." if path else "") + subcase.id
                self.resolve_case(subpath, subcase, case.sets, tests)

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

    def __init__(self, dir_path):
        """
        Initialize a database object.
        """
        assert self.is_dir_valid(dir_path)

        arches_schema = Reduction(Regex(), lambda x: [x], List(Regex()))

        base_optional_fields = dict(
            trees=Dict(
                Struct(required=dict(template=String()),
                       optional=dict(arches=arches_schema))
            ),
            arches=List(String()),
            components=Dict(String()),
            sets=Dict(String()),
            host_types=Dict(Class(HostType)),
            recipesets=Dict(List(String())),
            variables=Dict(
                Struct(required=dict(description=String()),
                       optional=dict(default=String()))
            ),
            origins=Dict(String()),
        )

        legacy_optional_fields = dict(
            **base_optional_fields,
            suites=List(YAMLFile(Class(Case))),
            host_type_regex=Regex(),
        )

        new_optional_fields = dict(
            **base_optional_fields,
            case=Choice(YAMLFile(Class(Case)),
                        Class(Case))
        )

        # TODO Remove once kpet-db transitions to universal cases
        def convert(data):
            data["case"] = dict(
                cases={
                    str(i): v for i, v in enumerate(data.pop("suites", []))
                }
            )
            if "host_type_regex" in data:
                data["case"]["host_type_regex"] = data.pop("host_type_regex")
            return data

        super().__init__(
            "database",
            ScopedYAMLFile(
                Succession(
                    Struct(optional=legacy_optional_fields),
                    convert,
                    Struct(optional=new_optional_fields)
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
        if self.variables is None:
            self.variables = dict()
        self.convert_tree_arches()
        self.resolve_case("", self.case, set(self.sets.keys()), set())
