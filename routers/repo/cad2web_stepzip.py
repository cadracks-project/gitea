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

r"""Conversion procedure of Gitea for CAD.

Called from Go code. The parameters are passed as command line arguments
in the Go code.

"""

from __future__ import print_function, absolute_import

import logging
from os import remove, mkdir
from os.path import basename, isdir


from aocutils.analyze.bounds import BoundingBox

# from osvcad.nodes import Part
from cadracks_core.factories import anchorable_part_from_stepzip

from cad2web_manage_files import _conversion_filename, _descriptor_filename, \
    _write_descriptor
from cad2web_convert_shape import _convert_shape


logger = logging.getLogger(__name__)


# TODO : how to display anchors?
def convert_stepzip_file(stepzip_filename: str,
                         target_folder: str,
                         remove_original: bool = True) -> None:
    r"""Convert an OsvCad Stepzip file for web display

    A Stepzip file contains a STEP geometry file and an anchors definition file
    zipped together

    Parameters
    ----------
    stepzip_filename : Full path to the Stepzip file
    target_folder : Full path to the target folder for the conversion
    remove_original : Should the input file be deleted after conversion?
        It should be deleted on a web platform to save disk space, but, for
        testing, it might be useful not to delete it.

    """
    if not isdir(target_folder):
        mkdir(target_folder)

    # part = Part.from_stepzip(stepzip_filename)
    # shape = part.node_shape.shape

    part = anchorable_part_from_stepzip(stepzip_filename)
    shape = part.shape

    converted_filename = _conversion_filename(stepzip_filename,
                                              target_folder,
                                              0)
    converted_basenames = [basename(converted_filename)]
    _convert_shape(shape, converted_filename)

    _write_descriptor(BoundingBox(shape).max_dimension,
                      converted_basenames,
                      _descriptor_filename(target_folder,
                                           basename(stepzip_filename)))
    if remove_original is True:
        remove(stepzip_filename)
