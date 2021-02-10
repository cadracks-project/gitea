#!/usr/bin/env python

# Copyright 2008-2015 Jelle Feringa (jelleferinga@gmail.com)
# Copyright 2018-2021 Guillaume Florent
#
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

from __future__ import print_function
from typing import Iterable, Tuple, List, Type

from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepTools import BRepTools_WireExplorer
from OCC.Core.TopAbs import (TopAbs_VERTEX, TopAbs_EDGE, TopAbs_FACE,
                             TopAbs_WIRE,
                             TopAbs_SHELL, TopAbs_SOLID, TopAbs_COMPOUND,
                             TopAbs_COMPSOLID)
from OCC.Core.TopExp import TopExp_Explorer, topexp_MapShapesAndAncestors
from OCC.Core.TopTools import (TopTools_ListOfShape,
                               TopTools_ListIteratorOfListOfShape,
                               TopTools_IndexedDataMapOfShapeListOfShape)
from OCC.Core.TopoDS import (topods, TopoDS_Wire, TopoDS_Vertex, TopoDS_Edge,
                             TopoDS_Face, TopoDS_Shell, TopoDS_Solid,
                             TopoDS_Compound, TopoDS_CompSolid, topods_Edge,
                             topods_Vertex, TopoDS_Iterator, TopoDS_Shape)
from OCC.Core.GCPnts import GCPnts_UniformAbscissa
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve


class WireExplorer:
    r"""Wire traversal"""
    def __init__(self, wire: TopoDS_Wire):
        assert isinstance(wire, TopoDS_Wire), 'not a TopoDS_Wire'
        self.wire = wire
        self.wire_explorer = BRepTools_WireExplorer(self.wire)
        self.done = False

    def _reinitialize(self) -> None:
        self.wire_explorer = BRepTools_WireExplorer(self.wire)
        self.done = False

    def _loop_topo(self, edges: bool = True) -> Iterable[Type[TopoDS_Shape]]:
        if self.done:
            self._reinitialize()
        topology_type = topods_Edge if edges else topods_Vertex
        seq = []
        hashes = []  # list that stores hashes to avoid redundancy
        occ_seq = TopTools_ListOfShape()
        while self.wire_explorer.More():
            # loop edges
            if edges:
                current_item = self.wire_explorer.Current()
            # loop vertices
            else:
                current_item = self.wire_explorer.CurrentVertex()
            current_item_hash = current_item.__hash__()
            if current_item_hash not in hashes:
                hashes.append(current_item_hash)
                occ_seq.Append(current_item)
            self.wire_explorer.Next()

        # Convert occ_seq to python list
        occ_iterator = TopTools_ListIteratorOfListOfShape(occ_seq)
        while occ_iterator.More():
            topo_to_add = topology_type(occ_iterator.Value())
            seq.append(topo_to_add)
            occ_iterator.Next()
        self.done = True
        return iter(seq)

    def ordered_edges(self) -> Iterable[TopoDS_Edge]:
        return self._loop_topo(edges=True)

    def ordered_vertices(self) -> Iterable[TopoDS_Vertex]:
        return self._loop_topo(edges=False)


class TopologyExplorer:
    r"""Topology traversal"""

    def __init__(self, my_shape: Type[TopoDS_Shape], ignore_orientation: bool = False):
        """Implements topology traversal from any TopoDS_Shape.

        This class lets you find how various topological entities are connected from one to another
        find the faces connected to an edge, find the vertices this edge is made from, get all faces connected to
        a vertex, and find out how many topological elements are connected from a source

        *note* when traversing TopoDS_Wire entities, its advised to use the specialized
        ``WireExplorer`` class, which will return the vertices / edges in the expected order

        :param my_shape: the shape which topology will be traversed

        :param ignore_orientation: filter out TopoDS_* entities of similar TShape but different Orientation

        for instance, a cube has 24 edges, 4 edges for each of 6 faces

        that results in 48 vertices, while there are only 8 vertices that have a unique
        geometric coordinate

        in certain cases ( computing a graph from the topology ) its preferable to return
        topological entities that share similar geometry, though differ in orientation
        by setting the ``ignore_orientation`` variable
        to True, in case of a cube, just 12 edges and only 8 vertices will be returned

        for further reference see TopoDS_Shape IsEqual / IsSame methods

        """
        self.myShape = my_shape
        self.ignore_orientation = ignore_orientation

        # the topoFactory dicts maps topology types and functions that can
        # create this topology
        self.topoFactory = {
            TopAbs_VERTEX: topods.Vertex,
            TopAbs_EDGE: topods.Edge,
            TopAbs_FACE: topods.Face,
            TopAbs_WIRE: topods.Wire,
            TopAbs_SHELL: topods.Shell,
            TopAbs_SOLID: topods.Solid,
            TopAbs_COMPOUND: topods.Compound,
            TopAbs_COMPSOLID: topods.CompSolid
        }
        self.topExp = TopExp_Explorer()

    def _loop_topo(self,
                   topology_type,
                   topological_entity=None,
                   topology_type_to_avoid=None) -> Iterable[Type[TopoDS_Shape]]:
        r"""This could be a faces generator for a python TopoShape class
        that way you can just do:
        for face in srf.faces:
            processFace(face)
        """
        topo_types = {TopAbs_VERTEX: TopoDS_Vertex,
                      TopAbs_EDGE: TopoDS_Edge,
                      TopAbs_FACE: TopoDS_Face,
                      TopAbs_WIRE: TopoDS_Wire,
                      TopAbs_SHELL: TopoDS_Shell,
                      TopAbs_SOLID: TopoDS_Solid,
                      TopAbs_COMPOUND: TopoDS_Compound,
                      TopAbs_COMPSOLID: TopoDS_CompSolid}

        assert topology_type in topo_types.keys(), f"{topology_type} not one of {topo_types.keys()}"
        # use self.myShape if nothing is specified
        if topological_entity is None and topology_type_to_avoid is None:
            self.topExp.Init(self.myShape, topology_type)
        elif topological_entity is None and topology_type_to_avoid is not None:
            self.topExp.Init(self.myShape, topology_type, topology_type_to_avoid)
        elif topology_type_to_avoid is None:
            self.topExp.Init(topological_entity, topology_type)
        elif topology_type_to_avoid:
            self.topExp.Init(topological_entity,
                             topology_type,
                             topology_type_to_avoid)
        seq = []
        hashes = []  # list that stores hashes to avoid redundancy
        occ_seq = TopTools_ListOfShape()
        while self.topExp.More():
            current_item = self.topExp.Current()
            current_item_hash = current_item.__hash__()

            if current_item_hash not in hashes:
                hashes.append(current_item_hash)
                occ_seq.Append(current_item)

            self.topExp.Next()
        # Convert occ_seq to python list
        occ_iterator = TopTools_ListIteratorOfListOfShape(occ_seq)
        while occ_iterator.More():
            topo_to_add = self.topoFactory[topology_type](occ_iterator.Value())
            seq.append(topo_to_add)
            occ_iterator.Next()

        if self.ignore_orientation:
            # filter out those entities that share the same TShape
            # but do *not* share the same orientation
            filter_orientation_seq = []
            for i in seq:
                _present = False
                for j in filter_orientation_seq:
                    if i.IsSame(j):
                        _present = True
                        break
                if _present is False:
                    filter_orientation_seq.append(i)
            return filter_orientation_seq
        else:
            return iter(seq)

    def faces(self) -> Iterable[TopoDS_Face]:
        r"""loops over all faces"""
        return self._loop_topo(TopAbs_FACE)

    def _number_of_topo(self, iterable: Iterable[Type[TopoDS_Shape]]) -> int:
        n = 0
        for _ in iterable:
            n += 1
        return n

    def number_of_faces(self) -> int:
        return self._number_of_topo(self.faces())

    def vertices(self) -> Iterable[TopoDS_Vertex]:
        r"""loops over all vertices"""
        return self._loop_topo(TopAbs_VERTEX)

    def number_of_vertices(self) -> int:
        return self._number_of_topo(self.vertices())

    def edges(self) -> Iterable[TopoDS_Edge]:
        r"""loops over all edges"""
        return self._loop_topo(TopAbs_EDGE)

    def number_of_edges(self) -> int:
        return self._number_of_topo(self.edges())

    def wires(self) -> Iterable[TopoDS_Wire]:
        r"""loops over all wires"""
        return self._loop_topo(TopAbs_WIRE)

    def number_of_wires(self):
        return self._number_of_topo(self.wires())

    def shells(self) -> Iterable[TopoDS_Shell]:
        r"""loops over all shells"""
        return self._loop_topo(TopAbs_SHELL, None)

    def number_of_shells(self) -> int:
        return self._number_of_topo(self.shells())

    def solids(self) -> Iterable[TopoDS_Solid]:
        r"""loops over all solids"""
        return self._loop_topo(TopAbs_SOLID, None)

    def number_of_solids(self) -> int:
        return self._number_of_topo(self.solids())

    def comp_solids(self) -> Iterable[TopoDS_CompSolid]:
        r"""loops over all compound solids"""
        return self._loop_topo(TopAbs_COMPSOLID)

    def number_of_comp_solids(self) -> int:
        return self._number_of_topo(self.comp_solids())

    def compounds(self) -> Iterable[TopoDS_Compound]:
        r"""loops over all compounds"""
        return self._loop_topo(TopAbs_COMPOUND)

    def number_of_compounds(self) -> int:
        return self._number_of_topo(self.compounds())

    def ordered_vertices_from_wire(self, wire: TopoDS_Wire) -> Iterable[TopoDS_Vertex]:
        r"""
        @param wire: TopoDS_Wire
        """
        we = WireExplorer(wire)
        return we.ordered_vertices()

    def number_of_ordered_vertices_from_wire(self, wire: TopoDS_Wire) -> int:
        return self._number_of_topo(self.ordered_vertices_from_wire(wire))

    def ordered_edges_from_wire(self, wire: TopoDS_Wire) -> Iterable[TopoDS_Edge]:
        """
        @param wire: TopoDS_Wire
        """
        we = WireExplorer(wire)
        return we.ordered_edges()

    def number_of_ordered_edges_from_wire(self, wire: TopoDS_Wire) -> int:
        return self._number_of_topo(self.ordered_edges_from_wire(wire))

    def _map_shapes_and_ancestors(self,
                                  topo_type_a,
                                  topo_type_b,
                                  topological_entity):
        """
        using the same method
        @param topo_type_a:
        @param topo_type_b:
        @param topological_entity:
        """
        topo_set = set()
        _map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp_MapShapesAndAncestors(self.myShape, topo_type_a, topo_type_b, _map)
        results = _map.FindFromKey(topological_entity)
        if results.IsEmpty():
            yield None

        topology_iterator = TopTools_ListIteratorOfListOfShape(results)
        while topology_iterator.More():

            topo_entity = self.topoFactory[topo_type_b](topology_iterator.Value())

            # return the entity if not in set
            # to assure we're not returning entities several times
            if topo_entity not in topo_set:
                if self.ignore_orientation:
                    unique = True
                    for i in topo_set:
                        if i.IsSame(topo_entity):
                            unique = False
                            break
                    if unique:
                        yield topo_entity
                else:
                    yield topo_entity

            topo_set.add(topo_entity)
            topology_iterator.Next()

    def _number_shapes_ancestors(self,
                                 topo_type_a,
                                 topo_type_b,
                                 topological_entity):
        """returns the number of shape ancestors
        If you want to know how many edges a faces has:
        _number_shapes_ancestors(self, TopAbs_EDGE, TopAbs_FACE, edg)
        will return the number of edges a faces has
        @param topo_type_a:
        @param topo_type_b:
        @param topological_entity:
        """
        topo_set = set()
        _map = TopTools_IndexedDataMapOfShapeListOfShape()
        topexp_MapShapesAndAncestors(self.myShape, topo_type_a, topo_type_b, _map)
        results = _map.FindFromKey(topological_entity)
        if results.IsEmpty():
            return None
        topology_iterator = TopTools_ListIteratorOfListOfShape(results)
        while topology_iterator.More():
            topo_set.add(topology_iterator.Value())
            topology_iterator.Next()
        return len(topo_set)

    # ======================================================================
    # EDGE <-> FACE
    # ======================================================================
    def faces_from_edge(self, edge: TopoDS_Edge) -> Iterable[TopoDS_Face]:
        """Faces that use the specified edge

        :param edge:
        :return:
        """
        return self._map_shapes_and_ancestors(TopAbs_EDGE, TopAbs_FACE, edge)

    def number_of_faces_from_edge(self, edge: TopoDS_Edge) -> int:
        """Number of faces that use the specified edge

        :param edge:
        :return:
        """
        return self._number_shapes_ancestors(TopAbs_EDGE, TopAbs_FACE, edge)

    def edges_from_face(self, face: TopoDS_Face) -> Iterable[TopoDS_Edge]:
        """Edges that make up a face

        :param face:
        :return:
        """
        return self._loop_topo(TopAbs_EDGE, face)

    def number_of_edges_from_face(self, face: TopoDS_Face) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_EDGE, face):
            cnt += 1
        return cnt

    # ======================================================================
    # VERTEX <-> EDGE
    # ======================================================================
    def vertices_from_edge(self, edg: TopoDS_Edge) -> Iterable[TopoDS_Vertex]:
        return self._loop_topo(TopAbs_VERTEX, edg)

    def number_of_vertices_from_edge(self, edg: TopoDS_Edge) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_VERTEX, edg):
            cnt += 1
        return cnt

    def edges_from_vertex(self, vertex: TopoDS_Vertex) -> Iterable[TopoDS_Edge]:
        return self._map_shapes_and_ancestors(TopAbs_VERTEX, TopAbs_EDGE,
                                              vertex)

    def number_of_edges_from_vertex(self, vertex: TopoDS_Vertex) -> int:
        return self._number_shapes_ancestors(TopAbs_VERTEX, TopAbs_EDGE, vertex)

    # ======================================================================
    # WIRE <-> EDGE
    # ======================================================================
    def edges_from_wire(self, wire: TopoDS_Wire) -> Iterable[TopoDS_Edge]:
        return self._loop_topo(TopAbs_EDGE, wire)

    def number_of_edges_from_wire(self, wire: TopoDS_Wire) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_EDGE, wire):
            cnt += 1
        return cnt

    def wires_from_edge(self, edg: TopoDS_Edge) -> Iterable[TopoDS_Wire]:
        return self._map_shapes_and_ancestors(TopAbs_EDGE, TopAbs_WIRE, edg)

    def wires_from_vertex(self, edg: TopoDS_Vertex) -> Iterable[TopoDS_Wire]:
        return self._map_shapes_and_ancestors(TopAbs_VERTEX, TopAbs_WIRE, edg)

    def number_of_wires_from_edge(self, edg: TopoDS_Edge) -> int:
        return self._number_shapes_ancestors(TopAbs_EDGE, TopAbs_WIRE, edg)

    # ======================================================================
    # WIRE <-> FACE
    # ======================================================================
    def wires_from_face(self, face: TopoDS_Face) -> Iterable[TopoDS_Wire]:
        return self._loop_topo(TopAbs_WIRE, face)

    def number_of_wires_from_face(self, face: TopoDS_Face) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_WIRE, face):
            cnt += 1
        return cnt

    def faces_from_wire(self, wire: TopoDS_Wire) -> Iterable[TopoDS_Face]:
        return self._map_shapes_and_ancestors(TopAbs_WIRE, TopAbs_FACE, wire)

    def number_of_faces_from_wires(self, wire: TopoDS_Wire) -> int:
        return self._number_shapes_ancestors(TopAbs_WIRE, TopAbs_FACE, wire)

    # ======================================================================
    # VERTEX <-> FACE
    # ======================================================================
    def faces_from_vertex(self, vertex: TopoDS_Vertex) -> Iterable[TopoDS_Face]:
        return self._map_shapes_and_ancestors(TopAbs_VERTEX, TopAbs_FACE,
                                              vertex)

    def number_of_faces_from_vertex(self, vertex: TopoDS_Vertex) -> int:
        return self._number_shapes_ancestors(TopAbs_VERTEX, TopAbs_FACE, vertex)

    def vertices_from_face(self, face: TopoDS_Face) -> Iterable[TopoDS_Vertex]:
        return self._loop_topo(TopAbs_VERTEX, face)

    def number_of_vertices_from_face(self, face: TopoDS_Face) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_VERTEX, face):
            cnt += 1
        return cnt

    # ======================================================================
    # FACE <-> SOLID
    # ======================================================================
    def solids_from_face(self, face: TopoDS_Face) -> Iterable[TopoDS_Solid]:
        return self._map_shapes_and_ancestors(TopAbs_FACE, TopAbs_SOLID, face)

    def number_of_solids_from_face(self, face: TopoDS_Face) -> int:
        return self._number_shapes_ancestors(TopAbs_FACE, TopAbs_SOLID, face)

    def faces_from_solids(self, solid: TopoDS_Solid) -> Iterable[TopoDS_Face]:
        return self._loop_topo(TopAbs_FACE, solid)

    def number_of_faces_from_solids(self, solid: TopoDS_Solid) -> int:
        cnt = 0
        for _ in self._loop_topo(TopAbs_FACE, solid):
            cnt += 1
        return cnt


def dump_topology_to_string(shape: TopoDS_Shape,
                            level: int = 0,
                            buffer: str = ""):
    """Prints the details of an object from the top down"""
    brt = BRep_Tool()
    s = shape.ShapeType()
    if s == TopAbs_VERTEX:
        pnt = brt.Pnt(topods_Vertex(shape))
        print(".." * level + f"<Vertex {hash(shape)}: {pnt.X()} {pnt.Y()} {pnt.Z()}>\n")
    else:
        print(".." * level, end="")
        print(shape_type_string(shape))
    it = TopoDS_Iterator(shape)
    while it.More() and level < 5:  # LEVEL MAX
        shp = it.Value()
        it.Next()
        print(dump_topology_to_string(shp, level + 1, buffer))


#
# Edge and wire discretizers
#

def discretize_wire(a_topods_wire: TopoDS_Wire) -> List[Tuple[float, float, float]]:
    """ Returns a set of points"""
    if not is_wire(a_topods_wire):
        raise AssertionError(
            "You must provide a TopoDS_Wire to the discretize_wire function.")
    wire_explorer = WireExplorer(a_topods_wire)
    wire_pnts = []
    # loop over ordered edges
    for edg in wire_explorer.ordered_edges():
        edg_pnts = discretize_edge(edg)
        wire_pnts += edg_pnts
    return wire_pnts


def discretize_edge(a_topods_edge: TopoDS_Edge,
                    deflection: float = 0.5) -> List[Tuple[float, float, float]]:
    """ Take a TopoDS_Edge and returns a list of points
    The more deflection is small, the more the discretization is precise,
    i.e. the more points you get in the returned points
    """
    if not is_edge(a_topods_edge):
        raise AssertionError("You must provide a TopoDS_Edge to the discretize_edge function.")
    edg = topods_Edge(a_topods_edge)
    if edg.IsNull():
        print("Warning : TopoDS_Edge is null. discretize_edge will return an empty list of points.")
        return []
    curve_adaptator = BRepAdaptor_Curve(edg)
    first = curve_adaptator.FirstParameter()
    last = curve_adaptator.LastParameter()

    discretizer = GCPnts_UniformAbscissa()
    discretizer.Initialize(curve_adaptator, deflection, first, last)

    assert discretizer.IsDone()
    assert discretizer.NbPoints() > 0

    points = []
    for i in range(1, discretizer.NbPoints() + 1):
        p = curve_adaptator.Value(discretizer.Parameter(i))
        points.append(p.Coord())
    return points


#
# TopoDS_Shape type utils
#
def shape_type_string(shape: TopoDS_Shape) -> str:
    """ Returns the type and id of any topods_shape
    shape: a TopoDS_Shape
    returns a string with the shape type and the shape id
    """
    shape_type = shape.ShapeType()
    types = {TopAbs_VERTEX: "Vertex",
             TopAbs_SOLID: "Solid",
             TopAbs_EDGE: "Edge",
             TopAbs_FACE: "Face",
             TopAbs_SHELL: "Shell",
             TopAbs_WIRE: "Wire",
             TopAbs_COMPOUND: "Compound",
             TopAbs_COMPSOLID: "Compsolid"}
    return f"{types[shape_type]} (id {hash(shape)})"


def is_vertex(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_VERTEX


def is_solid(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_SOLID


def is_edge(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_EDGE


def is_face(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_FACE


def is_shell(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_SHELL


def is_wire(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_WIRE


def is_compound(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_COMPOUND


def is_compsolid(topods_shape: TopoDS_Shape) -> bool:
    return topods_shape.ShapeType() == TopAbs_COMPSOLID
