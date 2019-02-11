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
import re
import os
import tempfile
import unittest
from kpet import targeted, data


class TargetedTest(unittest.TestCase):
    """Test cases for targeted."""
    def setUp(self):
        """Set common attributes used later on the test cases"""
        self.db_dir = os.path.join(os.path.dirname(__file__), 'assets')

    def test_get_patterns(self):
        """Check testcase patterns are read from the database"""
        expected_value = [
            {'pattern': re.compile('.*'), 'testcase_name': 'default/ltplite'},
            {'pattern': re.compile('^fs/ext4/.*'), 'testcase_name': 'fs/ext4'},
            {'pattern': re.compile('^fs/jbd2/.*'), 'testcase_name': 'fs/ext4'},
            {'pattern': re.compile('^fs/xfs/.*'), 'testcase_name': 'fs/xfs'},
            {'pattern': re.compile('^fs/[^/]*[ch]'),
             'testcase_name': 'fs/xfs'},
        ]
        self.assertListEqual(
            expected_value,
            targeted.get_patterns(data.Base(self.db_dir))
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
            'Kconfig',
            'fs/ext4/ext4.h',
            'fs/ext4/ext4_jbd2.h',
            'fs/ext4/inode.c',
            'fs/ext4/ioctl.c',
            'fs/xfs/xfs_log.c',
            'block/blk-core.c',
            'drivers/scsi/scsi_lib.c',
            'drivers/s390/scsi/zfcp_dbf.h',
            'drivers/s390/scsi/zfcp_fc.h',
            'drivers/s390/scsi/zfcp_fsf.h',
            'drivers/s390/scsi/zfcp_qdio.h',
            'drivers/s390/scsi/zfcp_reqlist.h',
            'lib/iomap.c',
            'lib/llist.c',
            'new_file',
            'Documentation/video-output.txt',
            'Documentation/video_output.txt',
        }
        self.assertSequenceEqual(
            expected_value,
            targeted.get_src_files(patches),
        )
        bad_patch_map = {
            # Empty
            b'':
            targeted.UnrecognizedPatchFormat,

            # No diff headers
            b'text':
            targeted.UnrecognizedPatchFormat,

            # Both files /dev/null
            b'--- /dev/null\n'
            b'+++ /dev/null':
            targeted.UnrecognizedPatchFormat,

            # Headers without files
            b'--- \n'
            b'+++ /dev/null':
            targeted.UnrecognizedPatchFormat,
            b'--- /dev/null\n'
            b'+++ ':
            targeted.UnrecognizedPatchFormat,

            # No directory
            b'--- abc\n'
            b'+++ ghi/jkl':
            targeted.UnrecognizedPatchPathFormat,
            b'--- abc/def\n'
            b'+++ jkl':
            targeted.UnrecognizedPatchPathFormat,

            # Directory diff
            b'--- abc/def\n'
            b'+++ ghi/jkl/':
            targeted.UnrecognizedPatchPathFormat,
            b'--- abc/def/\n'
            b'+++ ghi/jkl':
            targeted.UnrecognizedPatchPathFormat,

            # An absolute path to a file
            b'--- /abc/def\n'
            b'+++ ghi/jkl':
            targeted.UnrecognizedPatchPathFormat,
            b'--- abc/def\n'
            b'+++ /ghi/jkl':
            targeted.UnrecognizedPatchPathFormat,
        }
        for bad_patch, exception in bad_patch_map.items():
            with tempfile.NamedTemporaryFile() as bad_patch_file:
                bad_patch_file.write(bad_patch)
                bad_patch_file.flush()
                self.assertRaises(
                    exception,
                    targeted.get_src_files,
                    [bad_patch_file.name],
                )

    def test_get_test_cases(self):
        """Check getting test cases according to sources given"""
        database = data.Base(self.db_dir)
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite', 'fs/ext4'}),
            targeted.get_test_cases([], database)
        )
        src_files = {
            'fs/xfs/xfs_log.c',
        }
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite'}),
            targeted.get_test_cases(src_files, database)
        )
        src_files.add('fs/ext4/ext4.h')
        self.assertSequenceEqual(
            set({'fs/xfs', 'default/ltplite', 'fs/ext4'}),
            targeted.get_test_cases(src_files, database)
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
            list(targeted.get_all_test_cases(data.Base(self.db_dir)))
        )

    def test_get_property(self):
        """Check properties are returned by test name"""
        database = data.Base(self.db_dir)
        self.assertSequenceEqual(
            {'fs/xml/xfstests-ext4-4k.xml'},
            targeted.get_property('tasks', ['fs/ext4'], database)
        )
        self.assertSequenceEqual(
            {'default/xml/ltplite.xml', 'fs/xml/xfstests-ext4-4k.xml'},
            targeted.get_property('tasks', ['fs/ext4', 'default/ltplite'],
                                  database)
        )
        self.assertSequenceEqual(
            {'fs/xml/partitions.xml'},
            targeted.get_property('partitions', ['fs/xfs'], database)
        )
        self.assertSequenceEqual(
            {},
            targeted.get_property('tasks', [], database)
        )
        self.assertSequenceEqual(
            {},
            targeted.get_property('unknown', ['fs/xfs'], database)
        )
        self.assertRaises(KeyError, targeted.get_property, 'unknown',
                          ['fs/xfs'], database, required=True)
