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


r"""cad2web benchmark"""

from shutil import rmtree
import time
import uuid
from os.path import join, dirname
from typing import Callable

from cad2web_freecad import convert_freecad_file
from cad2web_neutral_formats import convert_step_file, convert_iges_file, \
    convert_brep_file, convert_stl_file
from cad2web_py import convert_py_file_part


def convert_timed(path: str, func: Callable) -> None:
    r"""Timed conversion and info message to stdout"""
    path = join(dirname(__file__), path)
    target_folder = join(dirname(__file__), f"tests/out/{uuid.uuid4()}")
    t0 = time.time()
    func(path, target_folder, remove_original=False)
    t1 = time.time()
    print(f"Conversion took {(t1 - t0):.3f} s for {path}")
    rmtree(target_folder, ignore_errors=True)


def main():
    r"""Run the benchmark"""
    print("**** BREP ****")
    convert_timed("tests/in/brep/cylinder_head.brep", convert_brep_file)
    convert_timed("tests/in/brep/Motor-c.brep", convert_brep_file)
    print("")

    print("**** FREECAD ****")
    convert_timed("tests/in/freecad/cyl_on_cube.FCStd", convert_freecad_file)
    # convert_timed("tests/in/freecad/wind_tunnel_complete_bellmouth.FCStd",
    #               convert_freecad_file)
    print("")

    print("**** IGES ****")
    convert_timed("tests/in/iges/aube_pleine.iges", convert_iges_file)
    convert_timed("tests/in/iges/box.igs", convert_iges_file)
    convert_timed("tests/in/iges/bracket.igs", convert_iges_file)
    print("")
    print("**** PY ****")
    convert_timed("tests/in/py/sample_projects/test_project/py_scripts/plate_with_holes.py",
                  convert_py_file_part)
    print("")

    print("**** STEP ****")
    convert_timed("tests/in/step/11752.stp", convert_step_file)
    convert_timed("tests/in/step/as1_pe_203.stp", convert_step_file)
    convert_timed("tests/in/step/bottle.stp", convert_step_file)
    print("")

    print("**** STL ****")
    convert_timed("tests/in/stl/box_ascii.stl", convert_stl_file)
    convert_timed("tests/in/stl/box_binary.stl", convert_stl_file)
    print("")


if __name__ == "__main__":
    main()
