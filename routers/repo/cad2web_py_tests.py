#!/usr/bin/env python
# coding: utf-8

# Copyright 2018-2021 Guillaume Florent

# This source file is part of the cadracks-project gitea fork (cad branch).
#
# The cad2web_*.py files is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# The cad2web_*.py files  are distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the cad2web_*.py files.  If not, see <https://www.gnu.org/licenses/>.

r"""Tests for cad2web_py.py"""

# import pytest

from shutil import rmtree

from os.path import join, dirname, isfile, basename

from cad2web_py import convert_py_file_shape
from cad2web_manage_files import _descriptor_filename


def test_convert_py_file_shape():
    r"""Test the conversion of a PY file that contains
    the definition of a part"""
    relpath = "tests/in/py/sample_projects/test_project/py_scripts/plate_with_holes.py"
    path_py_file_part = join(dirname(__file__), relpath)
    target_folder = join(dirname(__file__), "tests/out/plate_with_holes_py")
    convert_py_file_shape(path_py_file_part, target_folder, remove_original=False)
    assert isfile(_descriptor_filename(target_folder,
                                       basename(path_py_file_part)))
    rmtree(target_folder, ignore_errors=True)
