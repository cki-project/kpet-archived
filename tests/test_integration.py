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
"""Integration tests"""
import re
import sys
import os.path
import subprocess
import textwrap
import unittest
import shutil
import tempfile


# Initial command-line arguments invoking kpet
KPET_ARGV = []

# If running under "coverage"
if "coverage" in sys.modules:
    # Run our invocations of kpet under "coverage" as well to collect coverage
    # NOTE Keep command line in sync with tox.ini
    KPET_ARGV += "coverage run -p --branch --source=kpet".split(" ")

# Add path to in-tree kpet executable, relative for more readable output
KPET_ARGV += [os.path.relpath(os.path.join(os.path.dirname(__file__),
                                           "../bin/kpet"))]

COMMONTREE_XML = """
<job>
  {% for recipeset in RECIPESETS %}
    {% for HOST in recipeset %}
      HOST
      {% for suite in HOST.suites %}
        {{ suite.description }}
        {% for case in suite.cases %}
          {{ case.name }}
        {% endfor %}
      {% endfor %}
    {% endfor %}
  {% endfor %}
</job>
"""

EMPTYSUITEINDEX_YAML = """
host_types:
    normal: {}
host_type_regex: ^normal
recipesets:
    rcs1:
      - normal
arches:
    - arch
trees:
    tree: tree.xml
suites:
    - suite.yaml
"""


def get_db_path(db_name):
    """
    Return the database asset path for a database name.

    Args:
        db_name:  Database name (a subdir in the database asset directory).

    Returns:
        The full path to the database asset directory.
    """
    return os.path.relpath(os.path.join(os.path.dirname(__file__),
                                        "assets/db", db_name))


def get_patch_path(patch_name):
    """
    Return the patch asset path for a patch name.

    Args:
        patch_name: Patch name (a subdir in the patch asset directory).

    Returns:
        The full path to the patch asset directory.
    """
    return os.path.relpath(os.path.join(os.path.dirname(__file__),
                                        "assets/patches", patch_name))


def kpet(*args):
    """
    Execute kpet with specified arguments.

    Args:
        args:   Command-line arguments to pass to kpet.

    Returns:
        Exit status, standard output, standard error
    """
    process = subprocess.Popen(KPET_ARGV + list(args),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8")


def kpet_with_db(db_name, *args):
    """
    Execute kpet with a database specified by name, and optional extra
    arguments.

    Args:
        db_name:  Database name (a subdir in the database asset directory).
        args:     Extra command-line arguments to pass to kpet.

    Returns:
        Exit status, standard output, standard error
    """
    return kpet("--db", get_db_path(db_name), *args)


def kpet_run_generate(db_name, *args):
    """
    Execute "kpet run generate" with a database specified by name, tree
    "tree", architecture "arch", and kernel "kernel.tar.gz", and optional
    extra arguments.

    Args:
        db_name:    Database name (a subdir in the database asset directory).
        args:       Extra command-line arguments to pass to kpet.

    Returns:
        Exit status, standard output, standard error
    """
    return kpet_with_db(db_name,
                        "run", "generate", "-t", "tree",
                        "-k", "kernel.tar.gz", "-a", "arch", *args)


def create_asset_files(self, assets):
    for filename, content in assets.items():
        tmp_file = open(os.path.join(self.test_dir, filename), 'w')
        tmp_file.write(content)
        tmp_file.close()

    return str(self.test_dir)


class IntegrationTests(unittest.TestCase):
    """Integration tests"""

    # pylint: disable=invalid-name,no-self-use
    # (matching unittest conventions)
    def assertKpetProduces(self, func, *args,
                           status=0,
                           stdout_matching="",
                           stderr_matching=""):
        """
        Assert execution of a kpet-running function produces a particular exit
        status, and stderr/stdout output.

        Args:
            func:               Function executing kpet. Must return kpet's
                                exit status, stdout, and stderr.
            args:               Arguments to pass to "func".
            status:             Exit status kpet should produce.
                                Zero, if not specified.
            stdout_matching:    String representation of a regular expression,
                                which stdout should match fully.
                                "" if not specified.
            stderr_matching:    String representation of a regular expression,
                                which stderr should match fully.
                                "" if not specified.
        """
        errors = []
        result_status, result_stdout, result_stderr = func(*args)
        if result_status != status:
            errors.append("Expected exit status {}, got {}".
                          format(status, result_status))
        if not re.fullmatch(stdout_matching, result_stdout, re.DOTALL):
            errors.append("Stdout doesn't match regex \"{}\":\n{}".
                          format(stdout_matching,
                                 textwrap.indent(result_stdout, "    ")))
        if not re.fullmatch(stderr_matching, result_stderr, re.DOTALL):
            errors.append("Stderr doesn't match regex \"{}\":\n{}".
                          format(stderr_matching,
                                 textwrap.indent(result_stderr, "    ")))
        if errors:
            raise AssertionError("\n".join(errors))

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def assertKpetSrcMatchesTwoSuites(self, db_name):
        """
        Assert kpet source-matches two suites properly.

        Args:
            db_name:    Name of the database asset to test against.
        """
        # Both appear in baseline output
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # One appears with its patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Another appears with its patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # Both appear with their patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None appear with other patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def assertKpetSrcMatchesOneOfTwoSuites(self, db_name):
        """
        Assert kpet source-matches one of two suites properly.

        Args:
            db_name:    Name of the database asset to test against.
        """
        # Only one appears in baseline output
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # One appears with its patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Another doesn't appear with its patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')
        # Only one appears with both suite's patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # None appear with other patches
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def assertKpetSrcMatchesNoneOfTwoSuites(self, db_name):
        """
        Assert kpet source-matches none of two suites properly.

        Args:
            db_name:    Name of the database asset to test against.
        """
        # They don't appear in baseline output
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            stdout_matching=r'.*<job>\s*</job>.*')
        # They don't appear when all of their patches and extras are specified
        self.assertKpetProduces(
            kpet_run_generate, db_name,
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')
