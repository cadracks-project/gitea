#!/usr/bin/env python
# coding: utf-8

# Copyright 2018-2019 Guillaume Florent

# This source file is part of the present gitea fork (cad branch).
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

r"""Tests for cad2web_manage_files.py

Requires an internet connection to test the _download_file() function

"""

from os import remove
from os.path import isfile, join, dirname

import pytest

import requests

from cad2web_manage_files import _download_file, sha1


def test_download_file():
    r"""Test the download of a file that exists"""
    TEST_FILE_URL = "https://raw.githubusercontent.com/osv-team/pyosv/master/" \
                    "article.rst"
    TEST_FILE_NAME = join(dirname(__file__), "tmp_test.rst")
    _download_file(TEST_FILE_URL, TEST_FILE_NAME)
    assert isfile(TEST_FILE_NAME)
    remove(TEST_FILE_NAME)


def test_download_file_wrong_url():
    r"""Test the download of a file that does not exist"""
    TEST_FILE_URL = "https://raw.githubusercontent.com/osv-team/pyosv/" \
                    "master/a_r_t_i_c_l_e.rst"
    TEST_FILE_NAME = join(dirname(__file__), "tmp_test.rst")

    with pytest.raises(requests.exceptions.HTTPError):
        _download_file(TEST_FILE_URL, TEST_FILE_NAME)

    # Make sure no file is create
    assert not isfile(TEST_FILE_NAME)


def test_download_file_stupid_target():
    TEST_FILE_URL = "https://raw.githubusercontent.com/osv-team/pyosv/master/" \
                    "article.rst"
    TEST_FILE_NAME = join("/unknown/", "tmp_test.rst")
    with pytest.raises(FileNotFoundError):
        _download_file(TEST_FILE_URL, TEST_FILE_NAME)


def test_sha1():
    r"""Test the sha1() function on a file which content
    is supposed to be stable"""
    assert sha1(join(dirname(__file__), "topic.go")) == \
        "d42689f18e579fd70f155f8745bccf9487f1c5fe"


def test_sha1_non_existent_file():
    r"""Test sha1 for a file that does not exist"""
    with pytest.raises(FileNotFoundError):
        sha1(join(dirname(__file__), "unknown_file.go"))
