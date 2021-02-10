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

r"""Tests for cad2web_neutral_formats.py"""

# import pytest

from shutil import rmtree

from os.path import join, dirname, isfile, basename

from cad2web_stepzip import convert_stepzip_file
from cad2web_manage_files import _descriptor_filename


def test_convert_step_file():
    r"""Test the conversion of a STEP file"""
    relpath = "tests/in/py/sample_projects/car/shelf/wheel/CAR-WHEEL-RIM-D416_l174_mm---.stepzip"
    path_stepzip = join(dirname(__file__), relpath)
    target_folder = join(dirname(__file__), "tests/out/wheel_rim_stepzip")
    convert_stepzip_file(path_stepzip, target_folder, remove_original=False)
    assert isfile(_descriptor_filename(target_folder, basename(path_stepzip)))
    rmtree(target_folder, ignore_errors=True)
