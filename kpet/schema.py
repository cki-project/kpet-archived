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
"""Database schema"""

import re
import os
import yaml
from kpet.misc import format_exception_stack

# The type returned by re.compile(). Different between Python 2 and 3
# TODO Switch to just using re.Pattern once upgraded to Python 3.7 or later
RE = type(re.compile(""))


def _get_re_error_type():
    """
    Get the type of the exception produced when an invalid regular expression
    is compiled.

    Returns:
        The "invalid regular expression" exception type.
    Raises:
        Exception   when the type cannot be discovered.
    """
    try:
        re.compile("(")
    except Exception as exc:    # pylint: disable=broad-except
        return type(exc)
    raise Exception("\"Invalid regex\" exception type not found")


# The exception type produced by re.compile() on invalid regex.
# Different between Python 2 and 3, and unavailable directly in Python 2
# TODO Switch to just using re.error once upgraded to Python 3.7 or later
_ReError = _get_re_error_type()


class Invalid(Exception):
    """Invalid data exception"""


class Type:
    """
    Most basic schema validating the data to be an instance of specified
    type and resolving to the same.
    """
    def __init__(self, type):
        """
        Initialize a type schema.

        Args:
            type:   The type the data should be instance of.
        """
        self.type = type

    def validate(self, data):
        """
        Validate data according to the schema.

        Args:
            The data to validate.

        Raises:
            Invalid:    The data didn't match the schema.
        """
        if not isinstance(data, self.type):
            raise Invalid("Invalid type: {}, expecting {}".format(
                type(data).__name__, self.type.__name__
            ))

    def recognize(self):
        """
        Recognize the schema - return the schema that resolved data would
        have.

        Returns:
            The schema the resolved data would have.
        """
        return self

    def resolve(self, data):
        """
        Resolve (validate and massage) data according to the schema.

        Args:
            data:   The data to resolve.

        Returns:
            The resolved data. Will match the recognized schema.
        """
        self.validate(data)
        return data


class Choice(Type):
    """
    A schema matching a choice of other schemas.
    """
    def __init__(self, *args):
        """
        Initialize a choice schema.

        Args:
            args:   A list of schemas the data can match.
        """
        for arg in args:
            assert isinstance(arg, Type)
        super().__init__(object)
        self.schemas = args

    def validate(self, data):
        super().validate(data)
        exc_list = []
        # For each schema
        for schema in self.schemas:
            try:
                schema.validate(data)
                return
            except Invalid as exc:
                exc_list.append(exc)
        raise Invalid("\nand\n".join(format_exception_stack(exc)
                                     for exc in exc_list))

    def recognize(self):
        return Choice(*(schema.recognize() for schema in self.schemas))

    def resolve(self, data):
        self.validate(data)
        exc_list = []
        for schema in self.schemas:
            try:
                return schema.resolve(data)
            except Invalid as exc:
                exc_list.append(exc)
        raise Invalid("\nand\n".join(format_exception_stack(exc)
                                     for exc in exc_list))


class Attraction(Type):
    """
    An abstract schema describing an ordered list of schemas, optionally
    intermixed with data conversion functions of undefined purpose. Validates
    against one of the schemas, recognizes as the last schema in the list.
    Mnemonic: data is attracted to the ultimate schema.
    Cannot resolve data.
    """
    def __init__(self, *args):
        """
        Initialize an attraction schema.

        Args:
            args:   A list of schemas and data conversion functions.
                    Can be mixed in any order, except the first and the last
                    items must be schemas. Cannot be empty. Converter
                    functions must accept a data argument and return the
                    converted data.
        """
        assert args
        for arg in args:
            assert isinstance(arg, Type) or callable(arg)
        assert isinstance(args[0], Type)
        assert isinstance(args[-1], Type)
        super().__init__(object)
        self.schemas_and_converters = args

    def validate(self, data):
        super().validate(data)
        exc_list = []
        # For each schema/converter
        for schema_or_converter in self.schemas_and_converters:
            # If it's a schema
            if isinstance(schema_or_converter, Type):
                try:
                    schema_or_converter.validate(data)
                    return
                except Invalid as exc:
                    exc_list.append(exc)
        raise Invalid("\nand\n".join(format_exception_stack(exc)
                                     for exc in exc_list))

    def recognize(self):
        return self.schemas_and_converters[-1].recognize()

    def resolve(self, data):
        raise NotImplementedError()


class Succession(Attraction):
    """
    A schema describing a succession of accepted schema versions and the means
    to inherit the legacy data - converter functions. Validates against one of
    the schemas, recognizes as, and resolves to the last schema in the list.

    Each uninterrupted sequence of supplied converter functions must accept
    data validated by the preceding schema and return data validated by the
    following schema.
    """
    def resolve(self, data):
        self.validate(data)
        # Last valid schema
        last_valid_schema = None
        # We find the first matching schema, then proceed converting and
        # validating until we get to the last schema.
        # For each schema/converter in the succession
        for schema_or_converter in self.schemas_and_converters:
            # If it's a schema
            if isinstance(schema_or_converter, Type):
                try:
                    # Validate the data
                    schema_or_converter.validate(data)
                    last_valid_schema = schema_or_converter
                except Invalid:
                    # Cannot fail validation after a matching schema is found
                    assert last_valid_schema is None
            # Else it's a conversion function, and if we found valid schema
            elif last_valid_schema:
                # Convert the data for the next schema/converter
                data = schema_or_converter(data)
        # We should arrive at the last schema
        assert last_valid_schema is self.schemas_and_converters[-1]
        # Resolve the data with the last schema
        return last_valid_schema.resolve(data)


class Reduction(Attraction):
    """
    A schema describing a general schema and a choice of specific schemas for
    the same data, along with the means to convert the data from each of the
    specific schemas to the general one (converter functions). It essentially
    reduces a choice of schemas to one schema, hence the name. Validates
    against one of the schemas, recognizes as, and resolves to the last schema
    in the list (the general schema).

    Each uninterrupted sequence of supplied converter functions must accept
    data validated by the preceding (specific) schema and return data
    validated by the last schema in the list (the general schema).
    """
    def resolve(self, data):
        self.validate(data)
        # First valid schema
        first_valid_schema = None
        # We find the first matching schema, then run any following converters
        # until the next schema.
        for schema_or_converter in self.schemas_and_converters:
            # If it's a schema
            if isinstance(schema_or_converter, Type):
                # If we found our schema (and converted data) already
                if first_valid_schema:
                    break
                # Try to validate the data
                try:
                    schema_or_converter.validate(data)
                    first_valid_schema = schema_or_converter
                except Invalid:
                    pass
            # Else it's a conversion function, and if we found valid schema
            elif first_valid_schema:
                # Convert the data for the next converter/last schema
                data = schema_or_converter(data)
        # We should've matched a schema, guaranteed by validation
        assert first_valid_schema is not None
        # Resolve the data with the last schema
        return self.schemas_and_converters[-1].resolve(data)


class Null(Type):
    """Null schema"""
    def __init__(self):
        super().__init__(type(None))


class String(Type):
    """String schema"""
    def __init__(self, pattern="(.|\\n)*"):
        """
        Initialize a string schema.

        Args:
            pattern: Regular expression pattern the string must match as a
                     whole. Optional, the default matches anything.
        """
        super().__init__(str)
        assert isinstance(pattern, str)
        self.regex = re.compile(pattern)

    def validate(self, data):
        super().validate(data)
        if not self.regex.fullmatch(data):
            raise Invalid(
                f"String \"{data}\" doesn't match "
                f"regular expression \"{self.regex.pattern}\""
            )


class Int(Type):
    """Integer number schema"""
    def __init__(self):
        super().__init__(int)


class Float(Type):
    """Floating-point number schema"""
    def __init__(self):
        super().__init__(float)


class Boolean(Type):
    """Boolean schema"""
    def __init__(self):
        super().__init__(bool)


class Regex(String):
    """
    Regular expression string schema.
    """
    def validate(self, data):
        super().validate(data)
        try:
            re.compile(data)
        except _ReError:
            raise Invalid("Invalid regular expression")

    def recognize(self):
        return Type(RE)

    def resolve(self, data):
        self.validate(data)
        return re.compile(data)


class RelativeFilePath(String):
    """
    Relative file path schema, resolved to the same schema and absolute file
    path.
    """
    def resolve(self, data):
        self.validate(data)
        return os.path.abspath(data)


class YAMLFile(String):
    """
    YAML file path schema, resolved to the file contents according to
    specified schema.
    """
    def __init__(self, contents_schema):
        assert isinstance(contents_schema, Type)
        super().__init__()
        self.contents_schema = contents_schema

    def recognize(self):
        return self.contents_schema.recognize()

    def resolve(self, data):
        self.validate(data)
        file_path = os.path.abspath(data)

        # Load the data
        with open(file_path, "r") as resolved_data_file:
            resolved_data = yaml.safe_load(resolved_data_file)

        # Resolve loaded data
        try:
            return self.contents_schema.resolve(resolved_data)
        except Invalid:
            raise Invalid("Invalid contents of {}".format(file_path))


class ScopedYAMLFile(YAMLFile):
    """
    YAML file path schema, resolved to file contents according to specified
    schema, changes the current directory to the file's directory when
    resolving the contents.
    """
    def resolve(self, data):
        self.validate(data)
        file_path = os.path.abspath(data)
        dir_path = os.path.dirname(file_path)

        # Load the data
        with open(file_path, "r") as resolved_data_file:
            resolved_data = yaml.safe_load(resolved_data_file)

        # Validate and resolve loaded data
        orig_dir_path = os.getcwd()
        os.chdir(dir_path)
        try:
            return self.contents_schema.resolve(resolved_data)
        except Invalid:
            raise Invalid("Invalid contents of {}".format(file_path))
        finally:
            os.chdir(orig_dir_path)


class List(Type):
    """
    List schema, with every element matching a single specified schema.
    """
    def __init__(self, element_schema, min_len=0):
        """
        Initialize a List schema.

        Args:
            element_schema:  An instance of the specific Type type the list
                items should be instance of.
            min_len: Optional parameter to force the list to contain at least
                "min_len" elements. Defaults to 0.
        """
        assert isinstance(element_schema, Type)
        assert isinstance(min_len, int)
        assert min_len >= 0
        super().__init__(list)
        self.element_schema = element_schema
        self.min_len = min_len

    def validate(self, data):
        super().validate(data)

        if len(data) < self.min_len:
            raise Invalid(
                "This list must have at least {} elements, "
                "but only has {}!".format(self.min_len, len(data))
            )

        for index, value in enumerate(data):
            try:
                self.element_schema.validate(value)
            except Invalid:
                raise Invalid("Invalid value at index {}".format(index))

    def recognize(self):
        return List(self.element_schema.recognize())

    def resolve(self, data):
        self.validate(data)
        return [self.element_schema.resolve(value) for value in data]


# Default dictionary key schema
DICT_KEY_SCHEMA_DEFAULT = String()


class Dict(Type):
    """
    Dictionary schema, with separate schemas for all keys and all values.
    """
    def __init__(self, value_schema, key_schema=DICT_KEY_SCHEMA_DEFAULT):
        """
        Initialize a dictionary schema.

        Args:
            value_schema:   Schema for dictionary values.
            key_schema:     Schema for dictionary keys.
                            Optional. Default is String().
        """
        assert isinstance(key_schema, Type)
        assert isinstance(value_schema, Type)
        super().__init__(dict)
        self.key_schema = key_schema
        self.value_schema = value_schema

    def validate(self, data):
        super().validate(data)
        for key, value in data.items():
            try:
                self.key_schema.validate(key)
            except Invalid:
                raise Invalid("Invalid key \"{}\"".format(key))
            try:
                self.value_schema.validate(value)
            except Invalid:
                raise Invalid("Invalid value with key \"{}\"".format(key))

    def recognize(self):
        return Dict(self.value_schema.recognize())

    def resolve(self, data):
        self.validate(data)
        resolved_data = {}
        for key, value in data.items():
            resolved_data[key] = self.value_schema.resolve(value)
        return resolved_data


class Struct(Dict):
    """
    Dictionary schema, with string keys and each key having values with its
    own schema.
    """
    def __init__(self, required=None, optional=None):
        """
        Initialize a struct schema.

        Args:
            required:   A dictionary of keys required to be present in the
                        dictionary, mapped to their value schemas.
            optional:   A dictionary of keys that can be present in the
                        dictionary, but are not required, mapped to their
                        value schemas.
        """
        assert required is None or isinstance(required, dict)
        assert optional is None or isinstance(optional, dict)
        super().__init__(Type(object))
        if required is None:
            required = {}
        if optional is None:
            optional = {}
        for key, value in required.items():
            assert isinstance(key, str)
            assert isinstance(value, Type)
        for key, value in optional.items():
            assert isinstance(key, str)
            assert isinstance(value, Type)
        assert not (set(required.keys()) & set(optional.keys())), \
            "Some keys are both required and optional"
        self.required = required
        self.optional = optional

    def validate(self, data):
        super().validate(data)
        for name, schema in self.required.items():
            if name not in data:
                raise Invalid("Member \"{}\" is missing".format(name))
            value = data[name]
            try:
                schema.validate(value)
            except Invalid:
                raise Invalid("Member \"{}\" is invalid".format(name))
        for name, schema in self.optional.items():
            if name in data:
                value = data[name]
                try:
                    schema.validate(value)
                except Invalid:
                    raise Invalid("Member \"{}\" is invalid".format(name))
        for key in data.keys():
            if key not in self.required and key not in self.optional:
                raise Invalid("Unexpected member \"{}\" encountered".format(
                    key
                ))

    def recognize(self):
        recognized_required = {}
        recognized_optional = {}

        for name, schema in self.required.items():
            recognized_required[name] = schema.recognize()
        for name, schema in self.optional.items():
            recognized_optional[name] = schema.recognize()

        return Struct(required=recognized_required,
                      optional=recognized_optional)

    def resolve(self, data):
        self.validate(data)
        resolved_data = {}

        for name, schema in self.required.items():
            resolved_data[name] = schema.resolve(data[name])
        for name, schema in self.optional.items():
            if name in data:
                resolved_data[name] = schema.resolve(data[name])

        return resolved_data


class StrictStruct(Struct):
    """
    Struct schema with required keys only.
    """
    def __init__(self, **kwargs):
        super().__init__(required=kwargs)


class Class(Type):
    """
    Class instance schema, resolves to a class instance with (arbitrary) data
    as the creation argument.
    """
    def __init__(self, instance_type):
        super().__init__(object)
        self.instance_type = instance_type

    def recognize(self):
        return Type(object)

    def resolve(self, data):
        self.validate(data)
        return self.instance_type(data)
