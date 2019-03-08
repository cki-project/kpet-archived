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
import tempfile
import unittest
from kpet import targeted


class TargetedTest(unittest.TestCase):
    """Test cases for targeted."""
    def test_get_src_files(self):
        """
        Check filenames are extracted from the patches and also if it
        raises the UnrecognizedPatchFormat execption when the patch is not a
        git diff output.
        """
        patches_dir = os.path.join(os.path.dirname(__file__),
                                   'assets/patches/format_assortment')
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
