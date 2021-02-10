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

r"""Tests for cad2web_freecad.py"""

# import pytest

from shutil import rmtree

from os.path import join, dirname, isfile

from cad2web_freecad import name_file_visibility_from_unzipping_folder, \
    extract_fcstd, convert_freecad_file


def test_name_file_visibility_from_fcstd():
    r"""Test name file visibility tuples from known FCSTD file"""
    path_fcstd = join(dirname(__file__), "tests/in/freecad/cyl_on_cube.FCStd")
    target_folder = join(dirname(__file__), "tests/out/cyl_on_cube")
    extract_fcstd(path_fcstd, target_folder)
    nfv_tuples = name_file_visibility_from_unzipping_folder(target_folder)
    assert nfv_tuples == [('Box', 'PartShape.brp', True),
                          ('Cylinder', 'PartShape1.brp', True)]
    rmtree(target_folder, ignore_errors=True)


def test_conversion():
    path_fcstd = join(dirname(__file__), "tests/in/freecad/cyl_on_cube.FCStd")
    target_folder = join(dirname(__file__), "tests/out/cyl_on_cube")
    convert_freecad_file(path_fcstd, target_folder, remove_original=False)
    assert isfile(join(target_folder, "cyl_on_cube.FCStd.dat"))
    assert isfile(join(target_folder,
                       "1d9d48be363ddfcda883a17d9b6702248ad31f66_0.json"))
    assert isfile(join(target_folder,
                       "d1c0fade8eedaa3071fe85daa7ac946ca6a35146_1.json"))
    rmtree(target_folder, ignore_errors=True)


def test_conversion_trapezoidal_nut_crosssection():
    r"""One of the BREPs in the FCSTD contains a NULL shape,
    the conversion should proceed, using only BREPs with shapes
    that are not NULL"""
    path_fcstd = join(dirname(__file__),
                      "tests/in/freecad/Trapezoidal_nut_cross-section.fcstd")
    target_folder = join(dirname(__file__),
                         "tests/out/Trapezoidal_nut_cross-section")
    convert_freecad_file(path_fcstd, target_folder, remove_original=False)
    assert isfile(join(target_folder,
                       "Trapezoidal_nut_cross-section.fcstd.dat"))
    rmtree(target_folder, ignore_errors=True)
