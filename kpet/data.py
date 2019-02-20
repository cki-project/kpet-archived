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
import jinja2
from kpet.schema import Invalid, Int, Struct, StrictStruct, \
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
            if member_name in data:
                setattr(self, member_name, data[member_name])


class TestSuite(Object):    # pylint: disable=too-few-public-methods
    """Test suite"""
    def __init__(self, data):
        super().__init__(
            StrictStruct(
                description=String(),
                version=String(),
                patterns=List(StrictStruct(pattern=Regex(),
                                           testcase_name=String())),
                cases=List(
                    Struct(
                        required=dict(
                            name=String(),
                            tasks=String()
                        ),
                        optional=dict(
                            ignore_panic=Boolean(),
                            hostRequires=String(),
                            partitions=String(),
                            kickstart=String()
                        )
                    )
                )
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

    def __init__(self, dir_path):
        """
        Initialize a database object.
        """
        assert self.is_dir_valid(dir_path)
        super().__init__(
            ScopedYAMLFile(
                StrictStruct(
                    schema=StrictStruct(version=Int()),
                    testsuites=Dict(YAMLFile(Class(TestSuite))),
                    trees=Dict(String())
                )
            ),
            dir_path + "/index.yaml"
        )

        self.dir_path = dir_path

    def get_tree_template(self, tree_name):
        """
        Get the Jinja template instance for the tree with the specified name.
        The tree with such name must exist.

        Args:
            tree_name:  Name of the tree to get the template instance for.

        Returns:
            The tree instance.
        """
        assert tree_name in self.trees
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader([self.dir_path]),
            autoescape=jinja2.select_autoescape(
                enabled_extensions=('xml'),
                default_for_string=True,
            ),
        )
        return jinja_env.get_template(self.trees[tree_name])
