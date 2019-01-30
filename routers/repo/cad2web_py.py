#!/usr/bin/env python
# coding: utf-8

r"""Conversion procedure of Gitea for CAD.

Called from Go code. The parameters are passed as command line arguments
in the Go code.

"""

from __future__ import print_function, absolute_import

import imp
import logging
from os import remove, getcwd, chdir, system, mkdir
from os.path import splitext, basename, isdir
import sys


from aocutils.analyze.bounds import BoundingBox

from osvcad.nodes import Part

from cad2web_manage_files import _conversion_filename, _descriptor_filename, \
    _write_descriptor
from cad2web_convert_shape import _convert_shape


logger = logging.getLogger(__name__)


def convert_py_file_shape(py_filename, target_folder, remove_original=True):
    r"""Convert a PythonOCC script that contains a shape for web display

    Parameters
    ----------
    py_filename : str
        Full path to the Python file
    target_folder : str
        Full path to the target folder for the conversion
    remove_original : bool
        Should the input file be deleted after conversion?
        It should be deleted on a web platform to save disk space, but, for
        testing, it might be useful not to delete it.

    Returns
    -------
    Nothing, it is a procedure

    """
    if not isdir(target_folder):
        mkdir(target_folder)
    name, _ = splitext(basename(py_filename))
    module_ = imp.load_source(name, py_filename)

    shape = module_.__shape__
    converted_filename = _conversion_filename(py_filename,
                                              target_folder,
                                              0)
    converted_basenames = [basename(converted_filename)]
    _convert_shape(shape, converted_filename)

    _write_descriptor(BoundingBox(shape).max_dimension,
                      converted_basenames,
                      _descriptor_filename(target_folder,
                                           basename(py_filename)))
    if remove_original is True:
        remove(py_filename)


def convert_py_file_shapes(py_filename, target_folder, remove_original=True):
    r"""Convert a PythonOCC script that contains a list of shapes for web display

    Parameters
    ----------
    py_filename : str
        Full path to the Python file
    target_folder : str
        Full path to the target folder for the conversion
    remove_original : bool
        Should the input file be deleted after conversion?
        It should be deleted on a web platform to save disk space, but, for
        testing, it might be useful not to delete it.

    Returns
    -------
    Nothing, it is a procedure

    """
    if not isdir(target_folder):
        mkdir(target_folder)
    name, _ = splitext(basename(py_filename))
    module_ = imp.load_source(name, py_filename)

    shapes = module_.__shapes__

    converted_basenames = []

    # Determine the maximum spread in the list of shapes
    x_min_shapes, y_min_shapes, z_min_shapes, x_max_shapes, y_max_shapes, z_max_shapes = 1e6, 1e6, 1e6, -1e6, -1e6, -1e6
    for shape in shapes:
        x_min, y_min, z_min, x_max, y_max, z_max = BoundingBox(shape).as_tuple
        if x_min < x_min_shapes:
            x_min_shapes = x_min
        if y_min < y_min_shapes:
            y_min_shapes = y_min
        if z_min < z_min_shapes:
            z_min_shapes = z_min
        if x_max > x_max_shapes:
            x_max_shapes = x_max
        if y_max > y_max_shapes:
            y_max_shapes = y_max
        if z_max > z_max_shapes:
            z_max_shapes = z_max

    max_dim = max([x_max_shapes - x_min_shapes, y_max_shapes - y_min_shapes, z_max_shapes - z_min_shapes])

    for i, shape in enumerate(shapes):
        converted_filename = _conversion_filename(py_filename,
                                                  target_folder,
                                                  i)
        _convert_shape(shape, converted_filename)
        converted_basenames.append(basename(converted_filename))

    _write_descriptor(max_dim,
                      converted_basenames,
                      _descriptor_filename(target_folder,
                                           basename(py_filename)))
    if remove_original is True:
        remove(py_filename)


def convert_py_file_part(py_filename, target_folder, remove_original=True):
    r"""Convert an OsvCad Python file that contains a part for web display

    The Python file contains the definition of a part.

    Parameters
    ----------
    py_filename : str
        Full path to the Python file
    target_folder : str
        Full path to the target folder for the conversion
    remove_original : bool
        Should the input file be deleted after conversion?
        It should be deleted on a web platform to save disk space, but, for
        testing, it might be useful not to delete it.

    Returns
    -------
    Nothing, it is a procedure

    Raises
    ------
    ValueError if not a part definition

    """
    if not isdir(target_folder):
        mkdir(target_folder)
    part = Part.from_py_script(py_filename)
    shape = part.node_shape.shape
    converted_filename = _conversion_filename(py_filename,
                                              target_folder,
                                              0)
    converted_basenames = [basename(converted_filename)]
    _convert_shape(shape, converted_filename)

    _write_descriptor(BoundingBox(shape).max_dimension,
                      converted_basenames,
                      _descriptor_filename(target_folder,
                                           basename(py_filename)))
    if remove_original is True:
        remove(py_filename)


def convert_py_file_assembly(py_filename,
                             target_folder,
                             clone_url,
                             branch,
                             remove_original=True):
    r"""

    **** WORK IN PROGRESS ****

    Parameters
    ----------
    py_filename
    target_folder
    clone_url
    branch

    Returns
    -------

    """
    if not isdir(target_folder):
        mkdir(target_folder)

    logger.info("Dealing with a Python file that is supposed to "
                "define an assembly")
    # -1- change working dir to converted_files
    working_dir_initial = getcwd()
    chdir(target_folder)
    # 0 - Git clone
    logger.info("Git cloning %s into %s" % (clone_url, target_folder))

    # from subprocess import call
    # call(["cd", target_folder, "&&", "git", "clone", clone_url])
    system("cd %s && git clone %s" % (target_folder, clone_url))

    project = clone_url.split("/")[-1]

    # 1 - Git checkout the right branch/commit
    logger.info("Git checkout %s of %s" % (branch, project))
    system("cd %s/%s && git checkout %s" % (target_folder,
                                               project,
                                               branch))

    # 2 - Alter sys.path
    logger.info("Git checkout %s of %s" % (branch, project))
    sys_path_initial = sys.path
    path_extra = "%s/%s" % (target_folder, project)
    logger.info("Appending sys.path with %s" % path_extra)
    sys.path.append(path_extra)

    # Useless : adding converted_files to sys.path
    # logger.info("Appending sys.path with %s" % dirname(py_filename))
    # sys.path.append(dirname(py_filename))

    # 3 - Run osvcad functions
    converted_basenames = []
    # TODO : THE PROBLEM IS THAT WE ARE IMPORTING THE FILE OUTSIDE OF THE
    # CONTEXT OF ITS PROJECT
    module_ = imp.load_source(splitext(basename(py_filename))[0],
                              py_filename)
    assembly = getattr(module_, "assembly")

    for i, node in enumerate(assembly.nodes()):
        shape = node.node_shape.shape
        converted_filename = _conversion_filename(py_filename,
                                                  target_folder,
                                                  i)
        converted_basenames.append(basename(converted_filename))
        _convert_shape(shape, converted_filename)
    # TODO : max_dim
    _write_descriptor(1000,
                      converted_basenames,
                      _descriptor_filename(target_folder,
                                           basename(py_filename)))
    remove(py_filename)

    # 4 - Put sys.path back to where it was
    sys.path = sys_path_initial
    # 5 - Set back the working dir
    chdir(working_dir_initial)
    # 6 - Cleanup
    if remove_original is True:
        pass

    # TODO : remove folder created by git clone or the next clone will fail


def convert_py_file(py_filename,
                    target_folder,
                    clone_url,
                    branch,
                    remove_original=True):
    r"""Convert an OsvCad Python file for web display

    The Python file can contain the definition of a part or of an assembly

    Parameters
    ----------
    py_filename : str
        Full path to the Python file
    target_folder : str
        Full path to the target folder for the conversion

    Returns
    -------
    Nothing, it is a procedure

    """
    #  Determine which kind of Python file we are dealing with
    # Can be:
    # - a PythonOCC script that defines some shapes using the __shapes__ module level variable
    # - a Part definition Python script using the __part__ module level variable
    # - an Assembly definition Python script using the __assembly__ module level variable
    found_shape = False
    found_shapes = False
    found_part = False
    found_assembly = False

    with open(py_filename) as f:

        for line in f:
            if "__shape__" in line:
                found_shape = True
            if "__shapes__" in line:
                found_shapes = True
            if "__part__" in line:
                found_part = True
            if "__assembly__" in line:
                found_assembly = True

    # A geometry/part/assembly Python script can only define one thing at a time
    # e.g. it should no be possible to call for the visualization of a Part and of an Assembly in the same script
    l = [found_shape, found_shapes, found_part, found_assembly]
    if len(list(filter(lambda x: x is True, l))) > 1:
        raise RuntimeError("The Python script defines too many things")
    if len(list(filter(lambda x: x is True, l))) == 0:
        raise RuntimeError("The Python script defines nothing")

    # Call the right procedure depending on what is defined in the Python script
    if found_shape is True:
        convert_py_file_shape(py_filename,
                              target_folder,
                              remove_original=remove_original)

    if found_shapes is True:
        convert_py_file_shapes(py_filename,
                               target_folder,
                               remove_original=remove_original)

    if found_part is True:
        convert_py_file_part(py_filename,
                             target_folder,
                             remove_original=remove_original)

    if found_assembly is True:
        convert_py_file_assembly(py_filename,
                                 target_folder,
                                 clone_url,
                                 branch,
                                 remove_original=remove_original)
