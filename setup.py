#!/usr/bin/env python3
# Copyright (c) 2018 Red Hat, Inc. All rights reserved. This copyrighted
# material is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2 or later.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""Install kpet using setuptools."""
import sys
from setuptools import setup

python_required_major = 3
python_required_minor = 6

if sys.version_info.major < python_required_major or \
   sys.version_info.major == python_required_major and \
   sys.version_info.minor < python_required_minor:
    sys.stderr.write("Python v{}.{} is required, but running v{}.{}".
                     format(python_required_major, python_required_minor,
                            sys.version_info.major, sys.version_info.minor))
    sys.exit(1)

setup()
