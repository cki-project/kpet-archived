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
"""Test cases for patch module"""
import os
import tempfile
import unittest
from kpet import patch


class PatchTest(unittest.TestCase):
    """Test cases for patch module."""
    def test_success(self):
        """
        Check filenames are extracted from the patches successfully.
        """
        patches_dir = os.path.join(os.path.dirname(__file__),
                                   'assets/patches/format_assortment')
        patches = [os.path.join(patches_dir, p) for p in
                   sorted(os.listdir(patches_dir))]
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
            patch.location_set_get_src_set(patches),
        )

    def test_failure(self):
        """
        Check invalid patches fail to parse.
        """
        bad_patch_map = {
            # Empty
            b'':
            patch.UnrecognizedFormat,

            # No diff headers
            b'text':
            patch.UnrecognizedFormat,

            # Both files /dev/null
            b'--- /dev/null\n'
            b'+++ /dev/null':
            patch.UnrecognizedFormat,

            # Headers without files
            b'--- \n'
            b'+++ /dev/null':
            patch.UnrecognizedFormat,
            b'--- /dev/null\n'
            b'+++ ':
            patch.UnrecognizedFormat,

            # No directory
            b'--- abc\n'
            b'+++ ghi/jkl':
            patch.UnrecognizedPathFormat,
            b'--- abc/def\n'
            b'+++ jkl':
            patch.UnrecognizedPathFormat,

            # Directory diff
            b'--- abc/def\n'
            b'+++ ghi/jkl/':
            patch.UnrecognizedPathFormat,
            b'--- abc/def/\n'
            b'+++ ghi/jkl':
            patch.UnrecognizedPathFormat,

            # An absolute path to a file
            b'--- /abc/def\n'
            b'+++ ghi/jkl':
            patch.UnrecognizedPathFormat,
            b'--- abc/def\n'
            b'+++ /ghi/jkl':
            patch.UnrecognizedPathFormat,
        }
        for bad_patch, exception in bad_patch_map.items():
            with tempfile.NamedTemporaryFile() as bad_patch_file:
                bad_patch_file.write(bad_patch)
                bad_patch_file.flush()
                self.assertRaises(
                    exception,
                    patch.location_set_get_src_set,
                    [bad_patch_file.name],
                )
