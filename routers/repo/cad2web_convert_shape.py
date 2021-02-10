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

r"""OCC shape conversion to JSON"""

from __future__ import print_function, absolute_import

import json
import logging
from os.path import isfile
import uuid
from typing import Tuple, Iterable, Union

from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.Visualization import Tesselator

# from aocxchange.stl import StlExporter

# we use our own version of TopologyUtils.py as some functions were not
# available in the OCC that was installed
# from OCC.Extend.TopologyUtils import is_edge, is_wire, discretize_edge, \
#     discretize_wire
from cad2web_topology import is_edge, is_wire, discretize_edge, \
    discretize_wire, TopologyExplorer


logger = logging.getLogger(__name__)


def _convert_shape(shape: TopoDS_Shape, filename: str) -> None:
    r"""Convert a shape to a format usable for web display.

    The currently used format for web display is JSON

    Parameters
    ----------
    shape : OCC.Core.TopoDS.TopoDS_Shape
    filename : full path to the target file name

    """
    logger.debug("Call to _convert_shape()")
    if isfile(filename):
        logger.info("Using existing file")
        pass  # The cached version will be used
    else:
        logger.info("Converting shape")
        _shape_to_json(shape, filename)
    logger.debug("End of call to _convert_shape()")


def color_to_hex(rgb_color: Tuple[float, float, float]) -> str:
    """ Takes a tuple with 3 floats between 0 and 1.

    Useful to convert OCC colors to web color code

    Parameters
    ----------
    rgb_color : tuple of floats between 0. and 1.

    Returns
    -------
    Returns a hex.

    """
    r, g, b = rgb_color
    assert 0 <= r <= 1.
    assert 0 <= g <= 1.
    assert 0 <= b <= 1.
    rh = int(r * 255.)
    gh = int(g * 255.)
    bh = int(b * 255.)
    return "0x%.02x%.02x%.02x" % (rh, gh, bh)


def export_edgedata_to_json(edge_hash: str,
                            point_set: Iterable[Tuple[float, float, float]]) -> str:
    """ Export a set of points to a LineSegment buffergeometry

    Parameters
    ----------
    edge_hash
    point_set

    Returns
    -------
    A JSON string

    """
    # first build the array of point coordinates
    # edges are built as follows:
    # points_coordinates  =[P0x, P0y, P0z, P1x, P1y, P1z, P2x, P2y, etc.]
    points_coordinates = []
    for point in point_set:
        for coord in point:
            points_coordinates.append(coord)
    # then build the dictionary exported to json
    edges_data = {"metadata": {"version": 4.4,
                               "type": "BufferGeometry",
                               "generator": "pythonocc"},
                  "uuid": edge_hash,
                  "type": "BufferGeometry",
                  "data": {"attributes": {"position": {"itemSize": 3,
                                                       "type": "Float32Array",
                                                       "array": points_coordinates}
                                          }
                           }
                  }
    return json.dumps(edges_data)


# TODO: move control of color and appearance from HTML template to JSON
# TODO : separate the conversion from the IO
# TODO : why can the return value be either a bool or None (return value not even used in caller)
# TODO : if elif (no else ????)
def _shape_to_json(shape: TopoDS_Shape,
                   filename: str,
                   export_edges: bool = False,
                   color: Tuple[float, float, float] = (0.65, 0.65, 0.65),
                   specular_color: Tuple[float, float, float] = (1, 1, 1),
                   shininess: float = 0.9,
                   transparency: float = 0.,
                   line_color: Tuple[float, float, float] = (0, 0., 0.),
                   line_width: float = 2.,
                   mesh_quality: float = 1.) -> Union[bool, None]:
    r"""Converts a shape to a JSON file representation

    Parameters
    ----------
    shape : The OCC shape to convert
    filename : Full path to the file where the conversion is written
    export_edges : Should the edges be exported?
    color : RGB color (components from 0 to 1)
    specular_color : RGB color (components from 0 to 1)
    shininess : shininess from 0 to 1
    transparency : transparency specified from 0 to 1
    line_color : RGB color (components from 0 to 1)
    line_width : line width (unit ?)
    mesh_quality : mesh quality indicator

    Returns
    -------
    A boolean or None -> SOLVE THIS !

    """
    logger.info(f"Starting the conversion of a shape to JSON({filename})")
    _3js_shapes = {}
    _3js_edges = {}

    # if the shape is an edge or a wire, use the related functions
    if is_edge(shape):
        logger.debug("discretize an edge")
        pnts = discretize_edge(shape)
        edge_hash = "edg%s" % uuid.uuid4().hex
        str_to_write = export_edgedata_to_json(edge_hash, pnts)
        # edge_full_path = os.path.join(path, edge_hash + '.json')
        with open(filename, "w") as edge_file:
            edge_file.write(str_to_write)
        # store this edge hash
        _3js_edges[edge_hash] = [color, line_width]
        return True

    elif is_wire(shape):
        logger.debug("discretize a wire")
        pnts = discretize_wire(list(TopologyExplorer(shape).wires())[0])
        wire_hash = "wir%s" % uuid.uuid4().hex
        str_to_write = export_edgedata_to_json(wire_hash, pnts)
        # wire_full_path = os.path.join(path, wire_hash + '.json')
        with open(filename, "w") as wire_file:
            wire_file.write(str_to_write)
        # store this edge hash
        _3js_edges[wire_hash] = [color, line_width]
        return True

    shape_uuid = uuid.uuid4().hex
    shape_hash = "shp%s" % shape_uuid
    # tesselate
    tess = Tesselator(shape)
    tess.Compute(compute_edges=export_edges,
                 mesh_quality=mesh_quality,
                 uv_coords=False,
                 parallel=True)

    # export to 3JS
    # shape_full_path = os.path.join(path, shape_hash + '.json')
    # add this shape to the shape dict, sotres everything related to it
    _3js_shapes[shape_hash] = [export_edges,
                               color,
                               specular_color,
                               shininess,
                               transparency,
                               line_color,
                               line_width]
    # generate the mesh
    # tess.ExportShapeToThreejs(shape_hash, shape_full_path)
    # and also to JSON
    with open(filename, 'w') as json_file:
        json_file.write(tess.ExportShapeToThreejsJSONString(shape_uuid))

    # draw edges if necessary
    # if export_edges:
    #     # export each edge to a single json
    #     # get number of edges
    #     nbr_edges = tess.ObjGetEdgeCount()
    #     for i_edge in range(nbr_edges):
    #         # after that, the file can be appended
    #         str_to_write = ''
    #         edge_point_set = []
    #         nbr_vertices = tess.ObjEdgeGetVertexCount(i_edge)
    #         for i_vert in range(nbr_vertices):
    #             edge_point_set.append(tess.GetEdgeVertex(i_edge, i_vert))
    #         # write to file
    #         edge_hash = "edg%s" % uuid.uuid4().hex
    #         str_to_write += export_edgedata_to_json(edge_hash, edge_point_set)
    #         # create the file
    #         edge_full_path = os.path.join(path, edge_hash + '.json')
    #         with open(edge_full_path, "w") as edge_file:
    #             edge_file.write(str_to_write)
    #         # store this edge hash, with black color
    #         _3js_edges[hash] = [(0, 0, 0), line_width]
    logger.info("End of the conversion of a shape to JSON(%s)" % filename)


# def _convert_shape_stl(shape, filename):
#     r"""Write a shape to the converted file
#
#     NOT USED ANYMORE - DEPRECATED
#
#     Parameters
#     ----------
#     shape : OCC Shape
#         The input shape
#     filename : str
#         Path to the destination file
#
#     """
#     e = StlExporter(filename=filename, ascii_mode=False)
#     e.set_shape(shape)
#     e.write_file()
