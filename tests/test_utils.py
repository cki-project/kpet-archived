# Copyright (c) 2018 Red Hat, Inc. All rights reserved. This copyrighted
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
"""Test cases for utils module"""
import os
import unittest
from kpet import utils


class UtilsTest(unittest.TestCase):
    """Test cases for utils."""
    def setUp(self):
        """Set common attributes used later on the test cases"""
        self.root_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.template_rel_path = 'templates/rhel7.xml'

    def test_get_template_path(self):
        """
        Check the success case and if it raises the proper exception when
        the template is not found
        """
        self.assertEqual(
            self.template_rel_path,
            os.path.relpath(utils.get_template_path('rhel7', self.root_dir),
                            self.root_dir),
        )

        self.assertRaises(utils.TemplateNotFound,
                          utils.get_template_path, 'not-found', self.root_dir)

    def test_get_template_content(self):
        """
        Check the success case i.e. gets the actual content of the
        template.
        """
        template_path = os.path.join(self.root_dir, self.template_rel_path)
        with open(template_path) as template_handler:
            template_content = template_handler.read()
        self.assertEqual(
            template_content,
            utils.get_template_content('rhel7', self.root_dir)
        )
