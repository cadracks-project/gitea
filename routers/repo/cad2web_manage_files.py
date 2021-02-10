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

r"""Files paths and manipulation procedures of Gitea for CAD.

Called from Go code. The parameters are passed as command line arguments
in the Go code.

"""

from __future__ import print_function, absolute_import

import logging
import hashlib
from os.path import join
from typing import List

from requests import get

logger = logging.getLogger(__name__)


def _download_file(url: str, filename: str):
    r"""Download an external file (at specified url) to a local file

    Parameters
    ----------
    url : RL to the file to be downloaded
    filename : Full path to the local file that is to be created by the download

    Raises
    ------
    requests.exceptions.HTTPError if the URL points to a file
    that does not exist
    FileNotFoundError if the filename cannot be opened

    """
    logger.info(f"Downloading file at URL : {url}")
    response = get(url, stream=True)
    logger.info(f"Response is {response}")
    response.raise_for_status()

    with open(filename, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)


def sha1(filename: str) -> str:
    r"""Compute the SHA-1 hash of a file

    Parameters
    ----------
    filename : Full path to file

    Notes
    -----
    The typical call to this function takes 2-3 ms

    Returns
    -------
    str : The SHA-1 has of the file

    Raises
    ------
    FileNotFoundError if filename points to a file that does not exist

    """
    logger.debug(f"Computing SHA-1 hash of : {filename}")
    sha1sum = hashlib.sha1()
    with open(filename, 'rb') as source:
        block = source.read(2 ** 16)
        while len(block) != 0:
            sha1sum.update(block)
            block = source.read(2 ** 16)
    sha1_hash = sha1sum.hexdigest()
    logger.debug(f"SHA-1 hash is : {sha1_hash}")
    return sha1_hash


def _conversion_filename(file_in: str, folder_out: str, i: int = 0) -> str:
    r"""Build the name of the converted file using the name of the file to be
    converted

    Parameters
    ----------
    file_in : Path to the input_file
    folder_out : Path to the output folder
    i : Index, as a file may lead to the creation of many converted files
        if it contains multiple shapes

    Returns
    -------
    Path to the converted file

    """
    logger.debug("Call to _conversion_filename()")
    # return join(folder, "%s_%i.stl" % (name, i))

    hash_name = sha1(file_in)
    logger.debug("End of call to _conversion_filename()")
    return join(folder_out, f"{hash_name}_{i}.json")


def _descriptor_filename(converted_files_folder: str,
                         cad_file_basename: str) -> str:
    r"""Build the name of the file that contains the results of the
    conversion process.

    Parameters
    ----------
    converted_files_folder : Path to the folder where the converted files end up
    cad_file_basename : ase name of the CAD file that is being converted

    Returns
    -------
    Full path to the descriptor file

    """
    return join(converted_files_folder, f"{cad_file_basename}.dat")


def _write_descriptor(max_dim: float,
                      names: List[str],
                      descriptor_filename_: str) -> None:
    r"""Write the contents of a descriptor file.

    Parameters
    ----------
    max_dim : Maximum dimension of the bounding box of all objects in the CAD file
    names : lNames of all files that should be loaded by three.js to build the
        web display of the CAD file

    """
    with open(descriptor_filename_, 'w') as f:
        f.write(f"{max_dim}\n")
        f.write("\n".join(names))
