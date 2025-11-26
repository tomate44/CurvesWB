# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCADGui
import Part
from numpy import arange


class OrientedWire:
    def __init__(self, wire):
        self.wire = wire
        self.nb_edges = len(self.wire.OrderedEdges)
        self.edge_offset = 0
        self.direction = 1

    @property
    def edge_indices(self):
        return [i % self.nb_edges for i in arange(self.edge_offset,
                                                  self.edge_offset + self.direction * self.nb_edges,
                                                  self.direction)]

    def edge(self, i):
        return self.wire.OrderedEdges[int(self.edge_indices[i])]

    def vert_idx(self, v1, v2):
        i1 = False
        i2 = False
        for i, o in enumerate(self.wire.OrderedVertexes):
            if o.isPartner(v1):
                i1 = i
            elif o.isPartner(v2):
                i2 = i
        return i1, i2

    def similar_edges(self, e1, e2, tol=1e-3):
        if e1.isPartner(e2):
            # print("Partner edges")
            return True
        pa1 = e1.getParameterByLength(e1.Length / 2)
        pa2 = e2.getParameterByLength(e2.Length / 2)
        mp1 = e1.valueAt(pa1)
        mp2 = e2.valueAt(pa2)
        if (abs(e1.Length - e2.Length) < tol) and (mp1.distanceToPoint(mp2) < tol):
            # print("Midpoint match")
            return True
        # Part.show(Part.Compound([e1, e2]))
        return False

    def start_edges(self, e1, e2):
        "Orient the wire by defining e1 and e2 as first and second edges"
        _next = None
        off = None
        for i, o in enumerate(self.wire.OrderedEdges):
            if self.similar_edges(o, e1):
                off = i
            if self.similar_edges(o, e2):
                _next = i
        if (_next is None) or (off is None):
            # print(f"Error: failed to find edge index : {off} - {_next}")
            return False
        # print(f"Edge indices : {off} - {_next}")
        diff = _next - off
        self.edge_offset = off
        if diff > 0:
            self.direction = 1
        else:
            self.direction = -1
        if abs(diff) == len(self.wire.OrderedEdges) - 1:
            self.direction = -self.direction
        # print(f"Offset : {self.edge_offset} * {self.direction}")

    def start_vertexes(self, v1, v2):
        "Orient the wire by defining v1 and v2 as first and second vertexes"
        for i, o in enumerate(self.wire.OrderedEdges):
            if o.Vertex1.isPartner(v1) and o.Vertex2.isPartner(v2):
                self.edge_offset = i
            if o.Vertex1.isPartner(v2) and o.Vertex2.isPartner(v1):
                self.edge_offset = i
        i1, i2 = self.vert_idx(v1, v2)
        diff = i2 - i1
        if diff > 0:
            self.direction = 1
        else:
            self.direction = -1
        if abs(diff) == len(self.wire.OrderedVertexes) - 1:
            self.direction = -self.direction
        # print(f"Offset : {self.edge_offset} * {self.direction}")


class MatchWires:
    """Find the best vertex connections between two wires"""
    def __init__(self, w1, w2):
        self.w1 = OrientedWire(w1)
        self.w2 = OrientedWire(w2)
        self.sh1 = None
        self.sh2 = None
        self.nb_edges = min(len(w1.Edges), len(w2.Edges))

    @property
    def edge_pairs(self):
        pl = []
        for i in range(self.nb_edges):
            pl.append([self.w1.edge(i), self.w2.edge(i)])
        return pl

    @property
    def offset_code(self):
        return [self.w1.edge_offset,
                self.w2.edge_offset,
                self.w1.direction * self.w2.direction]

    @offset_code.setter
    def offset_code(self, v):
        self.w1.edge_offset = abs(v[0])
        self.w2.edge_offset = abs(v[1])
        self.w1.direction = 1
        self.w2.direction = v[2]

    def match_vertexes(self, vl1, vl2):
        self.w1.start_vertexes(vl1[0], vl1[1])
        self.w2.start_vertexes(vl2[0], vl2[1])

    def match_edges(self, el1, el2):
        n = min(len(el1), len(el2))
        for i in range(n - 1):
            self.w1.start_edges(el1[i], el1[i + 1])
            self.w2.start_edges(el2[i], el2[i + 1])

    def connect_subshapes(self, sl1, sl2):
        vl1 = [s for s in sl1 if isinstance(s, Part.Vertex)]
        vl2 = [s for s in sl2 if isinstance(s, Part.Vertex)]
        el1 = [s for s in sl1 if isinstance(s, Part.Edge)]
        el2 = [s for s in sl2 if isinstance(s, Part.Edge)]
        if len(el1) > 1 and len(el2) > 1:
            self.match_edges(el1, el2)
        elif len(vl1) > 1 and len(vl2) > 1:
            self.match_vertexes(vl1, vl2)
        return self.offset_code


def get_subs(s):
    el = []
    vl = []
    f = None
    for ss in s.SubObjects:
        if isinstance(ss, Part.Face):
            f = ss
        elif isinstance(ss, Part.Edge):
            el.append(ss)
        elif isinstance(ss, Part.Vertex):
            vl.append(ss)
    return f, el, vl


def test():
    s1, s2 = FreeCADGui.Selection.getSelectionEx()
    f1, el1, vl1 = get_subs(s1)
    f2, el2, vl2 = get_subs(s2)

    for w1, w2 in zip(f1.Wires, f2.Wires):
        mw = MatchWires(w1, w2)
        mw.match_vertexes(vl1, vl2)

        for pair in mw.edge_pairs:
            rs = Part.makeRuledSurface(*pair)
            Part.show(rs)

