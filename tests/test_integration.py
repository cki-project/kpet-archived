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
    "tree", architecture "arch", and kernel "kernel", and optional extra
    arguments.

    Args:
        db_name:    Database name (a subdir in the database asset directory).
        args:       Extra command-line arguments to pass to kpet.

    Returns:
        Exit status, standard output, standard error
    """
    return kpet_with_db(db_name,
                        "run", "generate", "-t", "tree",
                        "-k", "kernel", "-a", "arch", *args)


# pylint: disable=too-many-public-methods
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

    def test_empty_tree_list(self):
        """Test tree listing with empty database"""
        self.assertKpetProduces(kpet_with_db, "empty/db", "tree", "list")

    def test_empty_run_generate(self):
        """Test run generation with empty database"""
        self.assertKpetProduces(kpet_run_generate, "empty/db",
                                status=1,
                                stderr_matching=r'.*Tree "tree" not found.*')

    def test_minimal_run_generate(self):
        """Test run generation with empty database"""
        self.assertKpetProduces(kpet_run_generate, "minimal",
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_missing_tree_template_run_generate(self):
        """Test run generation with a missing tree template"""
        self.assertKpetProduces(kpet_run_generate,
                                "invalid/semantics/missing_tree_template",
                                "-t", "missing_template",
                                status=1,
                                stderr_matching=r'.*TemplateNotFound.*')

    def test_missing_suite_file_run_generate(self):
        """Test run generation with a missing suite file"""
        self.assertKpetProduces(kpet_run_generate,
                                "invalid/semantics/missing_suite_file",
                                status=1,
                                stderr_matching=r'.*missing.yaml.*')

    def test_missing_case_run_generate(self):
        """Test run generation with a pattern pointing to a missing case"""
        # NOTE This is not correct, but it's what we do for now
        # TODO Abort kpet if a case is missing, likely on schema validation
        self.assertKpetProduces(kpet_run_generate,
                                "invalid/semantics/missing_case",
                                get_patch_path("misc/files_abc.diff"),
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_invalid_top_yaml_tree_list(self):
        """Test tree listing with invalid YAML in the top database file"""
        self.assertKpetProduces(kpet_with_db, "invalid/yaml/top",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_suite_yaml_tree_list(self):
        """Test tree listing with invalid YAML in a suite file"""
        self.assertKpetProduces(kpet_with_db, "invalid/yaml/suite",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*yaml.parser.ParserError.*')

    def test_invalid_top_data_tree_list(self):
        """Test tree listing with invalid data in the top database file"""
        self.assertKpetProduces(kpet_with_db, "invalid/data/top",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Base data.*')

    def test_invalid_suite_data_tree_list(self):
        """Test tree listing with invalid data in a suite file"""
        self.assertKpetProduces(kpet_with_db, "invalid/data/suite",
                                "tree", "list",
                                status=1,
                                stderr_matching=r'.*Invalid Suite data.*')

    def test_empty_suite_run_generate(self):
        """Test run generation with an empty suite"""
        self.assertKpetProduces(kpet_run_generate, "empty/suite",
                                stdout_matching=r'.*<job>\s*</job>.*')

    def test_empty_case_no_patterns_run_generate(self):
        """Test run generation with an empty test case without patterns"""
        self.assertKpetProduces(
            kpet_run_generate, "empty/case_no_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_empty_case_with_a_pattern_run_generate(self):
        """Test run generation with an empty test case with a pattern"""
        self.assertKpetProduces(
            kpet_run_generate, "empty/case_with_a_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')

    def test_match_sources_one_case_no_patterns(self):
        """Test source-matching a case with no patterns"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/no_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/no_patterns",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_one_case_one_pattern(self):
        """Test source-matching a case with one pattern"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches patches it should
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/one_pattern",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_one_case_two_patterns(self):
        """Test source-matching a case with two patterns"""
        # Matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches first patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches second patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Matches both patches only once
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Doesn't match patches it shouldn't
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/one_case/two_patterns",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_cases(self):
        """Test source-matching two cases"""
        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*'
                            r'case1\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_cases",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_two_suites(self):
        """Test source-matching two suites"""
        # Both match baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # Both match their patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/two_suites",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_db(self):
        """Test source-matching with a specific db"""
        # Nothing matches baseline in a specific db
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/db",
            stdout_matching=r'.*<job>\s*</job>.*')
        # Only appropriate case matches with a patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/db",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # All cases can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/db",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/db",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_suite(self):
        """Test source-matching with a specific suite"""
        # Only non-specific suite matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All suites can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/suite",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_match_sources_specific_case(self):
        """Test source-matching with a specific case"""
        # Only non-specific case matches baseline
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # First matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_abc.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*</job>.*')
        # Second matches its patch
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite2\s*case2\s*</job>.*')
        # All cases can match if provided appropriate patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_abc.diff"),
            get_patch_path("misc/files_def.diff"),
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
        # None match other patches
        self.assertKpetProduces(
            kpet_run_generate, "match/sources/specific/case",
            get_patch_path("misc/files_ghi.diff"),
            stdout_matching=r'.*<job>\s*</job>.*')

    def test_multihost_no_types_no_regex_no_suites(self):
        """Test multihost support without types/regex/suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/no_types/no_regex/no_suites")

    def test_multihost_no_types_no_regex_two_suites(self):
        """Test multihost support without types/regex and two suites"""
        self.assertKpetSrcMatchesTwoSuites(
            "multihost/no_types/no_regex/two_suites")

    def test_multihost_no_types_wildcard_regex_two_suites(self):
        """
        Test multihost support without types, with a DB-level wildcard regex,
        and two suites.
        """
        self.assertKpetSrcMatchesTwoSuites("multihost/no_types/db_regex")

    def test_multihost_one_type_no_regex_no_suites(self):
        """Test multihost support with one type, but no regex/suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/one_type/no_regex/no_suites")

    def test_multihost_one_type_no_regex_two_suites(self):
        """Test multihost support with one type, no regex, and two suites"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/one_type/no_regex/two_suites")

    def test_multihost_one_type_db_regex(self):
        """Test multihost support with one type and DB-level regex"""
        self.assertKpetSrcMatchesTwoSuites("multihost/one_type/db_regex")

    def test_multihost_one_type_suite_regex(self):
        """Test multihost support with one type and suite-level regexes"""
        self.assertKpetSrcMatchesOneOfTwoSuites(
            "multihost/one_type/suite_regex")

    def test_multihost_one_type_case_regex(self):
        """Test multihost support with one type and case-level regexes"""
        self.assertKpetSrcMatchesOneOfTwoSuites(
            "multihost/one_type/case_regex")

    def test_multihost_one_type_wrong_regex(self):
        """Test multihost support with one type a wrong DB-level regex"""
        self.assertKpetSrcMatchesNoneOfTwoSuites(
            "multihost/one_type/wrong_regex")

    def test_multihost_two_types_one_case_each(self):
        """Test multihost support with two types matching one case each"""
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/one_case_each",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'HOST\s*suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_first(self):
        """
        Test multihost support with two types and both cases matching the
        first one.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_first",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_second(self):
        """
        Test multihost support with two types and both cases matching the
        second one.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_second",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')

    def test_multihost_two_types_both_cases_both(self):
        """
        Test multihost support with two types and both cases matching both
        types.
        """
        # TODO Distinguish host types somehow
        self.assertKpetProduces(
            kpet_run_generate, "multihost/two_types/both_cases_both",
            stdout_matching=r'.*<job>\s*HOST\s*suite1\s*case1\s*'
                            r'suite2\s*case2\s*</job>.*')
