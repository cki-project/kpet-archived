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
"""Test cases for targeted module"""
import os
import json
import tempfile
import unittest
from kpet import targeted


class TargetedTest(unittest.TestCase):
    """Test cases for targeted."""
    def setUp(self):
        """Set common attributes used later on the test cases"""
        self.db_dir = os.path.join(os.path.dirname(__file__), 'assets')

    def test_get_patterns_by_layout(self):
        """Check patterns are readed from the layout"""
        layout_path = os.path.join(self.db_dir, 'layout', 'layout.json')
        with open(layout_path) as file_handler:
            layout = json.load(file_handler)['testsuites']
        expected_value = [
            {'pattern': '.*', 'testcase_name': 'default/ltplite'},
            {'pattern': '^fs/ext4/.*', 'testcase_name': 'fs/ext4'},
            {'pattern': '^fs/jbd2/.*', 'testcase_name': 'fs/ext4'},
            {'pattern': '^fs/xfs/.*', 'testcase_name': 'fs/xfs'},
            {'pattern': '^fs/[^/]*[ch]', 'testcase_name': 'fs/xfs'},
        ]
        self.assertListEqual(
            expected_value,
            targeted.get_patterns_by_layout(layout, self.db_dir)
        )

    def test_get_src_files(self):
        """
        Check filenames are extracted from the patches and also if it
        raises the UnrecognizedPatchFormat execption when the patch is not a
        git diff output.
        """
        patches_dir = os.path.join(self.db_dir, 'patches')
        patches = []
        for patch in sorted(os.listdir(patches_dir)):
            patches.append(os.path.join(patches_dir, patch))
        expected_value = {
            'fs/ext4/ext4.h',
            'fs/ext4/ext4_jbd2.h',
            'fs/ext4/inode.c',
            'fs/ext4/ioctl.c',
            'fs/xfs/xfs_log.c',
        }
        self.assertSequenceEqual(
            expected_value,
            targeted.get_src_files(patches),
        )
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(b'Unrecognized format patch')
            tmpfile.flush()
            patches = [tmpfile.name]
            self.assertRaises(
                targeted.UnrecognizedPatchFormat,
                targeted.get_src_files,
                patches,
            )

    def test_get_test_cases(self):
        """Check getting test cases according to sources given"""
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite', 'fs/ext4'}),
            targeted.get_test_cases([], self.db_dir)
        )
        src_files = {
            'fs/xfs/xfs_log.c',
        }
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite'}),
            targeted.get_test_cases(src_files, self.db_dir)
        )
        src_files.add('fs/ext4/ext4.h')
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite', 'fs/ext4'}),
            targeted.get_test_cases(src_files, self.db_dir)
        )

    def test_get_all_test_cases(self):
        """Check all test cases in the database are returned"""
        expected_value = [
            {
                'name': 'default/ltplite',
                'tasks': 'default/xml/ltplite.xml',
            },
            {
                'name': 'fs/ext4',
                'tasks': 'fs/xml/xfstests-ext4-4k.xml',
                'hostRequires': 'fs/xml/hostrequires.xml',
            },
            {
                'name': 'fs/xfs',
                'tasks': 'fs/xml/xfstests-xfs-4k-finobt.xml',
                "partitions": 'fs/xml/partitions.xml',
            },
        ]
        self.assertListEqual(
            expected_value,
            list(targeted.get_all_test_cases(self.db_dir))
        )

    def test_get_tasks(self):
        """Check tasks template paths are returned by test name"""
        self.assertSequenceEqual(
            {'fs/xml/xfstests-ext4-4k.xml'},
            targeted.get_tasks(['fs/ext4'], self.db_dir)
        )
        self.assertSequenceEqual(
            {'default/xml/ltplite.xml', 'fs/xml/xfstests-ext4-4k.xml'},
            targeted.get_tasks(['fs/ext4', 'default/ltplite'], self.db_dir)
        )
        self.assertSequenceEqual(
            {},
            targeted.get_tasks([], self.db_dir)
        )

    def test_get_host_requires(self):
        """Check host requires template paths are returned by test name"""
        self.assertSequenceEqual(
            {'fs/xml/hostrequires.xml'},
            targeted.get_host_requires(['fs/ext4'], self.db_dir)
        )
        self.assertSequenceEqual(
            {},
            targeted.get_host_requires(['fs/xfs'], self.db_dir)
        )

    def test_get_partitions(self):
        """Check partitions template paths are returned by test name"""
        self.assertSequenceEqual(
            {'fs/xml/partitions.xml'},
            targeted.get_partitions(['fs/xfs'], self.db_dir)
        )
        self.assertSequenceEqual(
            {},
            targeted.get_partitions(['fs/ext4'], self.db_dir)
        )
