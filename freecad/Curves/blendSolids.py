# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
from . import _utils
from . import blend_curve as bc
from .nurbs_tools import nurbs_quad
from .match_wires import MatchWires
from math import cos


def get_link_torsion(w1, w2, offset, rev=1):
    num = min(len(w1.Vertexes), len(w2.Vertexes))
    angle_len = 0
    for i in range(num):
        idx = (i + offset) % num
        v1 = w1.OrderedVertexes[idx]
        e1 = w1.OrderedEdges[idx]
        tan1 = e1.Curve.tangent(e1.Curve.parameter(v1.Point))[0]
        v2 = w2.OrderedVertexes[i * rev]
        e2 = w2.OrderedEdges[i * rev]
        tan2 = e2.Curve.tangent(e2.Curve.parameter(v2.Point))[0]
        cv = v2.Point - v1.Point
        angle_len += abs(cos(cv.getAngle(tan1)))
        angle_len += abs(cos(cv.getAngle(tan2)))
    return angle_len


def get_link_size(w1, w2, offset, rev=1):
    num = min(len(w1.Vertexes), len(w2.Vertexes))
    sum_len = 0
    for i in range(num):
        idx = (i + offset) % num
        sum_len += w1.OrderedVertexes[idx].Point.distanceToPoint(w2.OrderedVertexes[i * rev].Point)
    return sum_len


def get_vertex_offset(w1, w2, torsion=True):
    if torsion:
        func = get_link_torsion
    else:
        func = get_link_size
    num = min(len(w1.Vertexes), len(w2.Vertexes))
    lenlist = []
    for offset in range(num):
        lenlist.append(func(w1, w2, offset, rev=-1))
    for offset in range(num):
        lenlist.append(func(w1, w2, offset, rev=1))
    offset = lenlist.index(min(lenlist)) - num
    lenlist.sort()
    error = (lenlist[0] / lenlist[1])
    return offset, error


def get_selection_data(sel):
    res = []
    for so in sel:
        f = None
        v = []
        for sub in so.SubObjects:
            if isinstance(sub, Part.Face):
                f = sub
            elif isinstance(sub, Part.Vertex):
                v.append(sub)
        res.append([so.Object.Shape, f, v])
    return res


def other_face(sh, f, e):
    try:
        anc = sh.ancestorsOfType(e, Part.Face)
    except Part.OCCError:
        print("ancestorsOfType Failed")
        anc = []
    for af in anc:
        if not af.isPartner(f):
            return af


def other_edge(sh, f, v):
    sh_anc = sh.ancestorsOfType(v, Part.Edge)
    f_anc = f.ancestorsOfType(v, Part.Edge)
    for e1 in sh_anc:
        found = False
        for e2 in f_anc:
            if e1.isPartner(e2):
                found = True
        if not found:  # e1 doesn't belong to face
            return e1
    return False


def external_edge(sh, f, v):
    line = Part.Line()
    line.Location = v.Point
    e = other_edge(sh, f, v)
    p = e.Curve.parameter(v.Point)
    fp = e.Curve.FirstParameter
    lp = e.Curve.LastParameter
    if abs(p - fp) > abs(p - lp):
        line.Direction = e.Curve.tangent(p)[0]
    else:
        line.Direction = -e.Curve.tangent(p)[0]
    return line


def external_edges(sh, f, length=1e20):
    lines = []
    for w in f.Wires:
        w_lines = []
        for v in w.OrderedVertexes:
            w_lines.append(external_edge(sh, f, v).toShape(0, length))
        lines.append(w_lines)
    return lines


def offset_index(i, offset, num):
    if offset < 0:
        return (num - i + offset) % num
    else:
        return (i + offset) % num


def get_poly_data(sh1, f1, w1, sh2, f2, w2, offset):
    if not len(w1.Vertexes) == len(w2.Vertexes):
        return
    num = len(w1.Edges)
    score = 0
    # print(f"Offset : {offset}")
    idx = offset_index(0, offset, num)
    v1 = w1.OrderedVertexes[0]
    v2 = w2.OrderedVertexes[idx]
    # e1 = external_edge(sh1, f1, v1).toShape(0, 1e20)
    # e2 = external_edge(sh2, f2, v2).toShape(0, 1e20)
    # d, pts, info = e1.distToShape(e2)
    # p1, p2 = pts[0]
    # d1 = e1.valueAt(0).distanceToPoint(p1)
    # d2 = p2.distanceToPoint(e2.valueAt(0))
    # print(f"Vertex{i}-Vertex{idx} : {d1} / {d} / {d2}")
    # score += d / (min([d1, d2]) or 1e50)
    l1 = external_edge(sh1, f1, v1)
    l2 = external_edge(sh2, f2, v2)
    plane_normal = 0.5 * (l1.Direction - l2.Direction)
    plane1 = Part.Plane(v1.Point, plane_normal)
    plane2 = Part.Plane(v2.Point, plane_normal)
    pts1 = []
    pts2 = []
    for j in range(num):
        idx2 = offset_index(j, offset, num)
        v3 = w1.OrderedVertexes[j]
        v4 = w2.OrderedVertexes[idx2]
        u1, v1 = plane1.parameter(v3.Point)
        u2, v2 = plane2.parameter(v4.Point)
        pts1.append(FreeCAD.Vector(u1, v1))
        pts2.append(FreeCAD.Vector(u2, v2))
    poly1 = Part.makePolygon(pts1)
    poly2 = Part.makePolygon(pts2)
    bb1 = poly1.BoundBox
    bb2 = poly2.BoundBox
    u0, u1, v0, v1 = (bb1.XMin, bb1.XMax, bb1.YMin, bb1.YMax)
    s0, s1, t0, t1 = (bb2.XMin, bb2.XMax, bb2.YMin, bb2.YMax)
    poles1 = [[FreeCAD.Vector(u0, v0, 0), FreeCAD.Vector(u0, v1, 0)],
              [FreeCAD.Vector(u1, v0, 0), FreeCAD.Vector(u1, v1, 0)]]
    poles2 = [[FreeCAD.Vector(s0, t0, 0), FreeCAD.Vector(s0, t1, 0)],
              [FreeCAD.Vector(s1, t0, 0), FreeCAD.Vector(s1, t1, 0)]]
    quad1 = nurbs_quad(poles1, param_range=[0.0, 1.0, 0.0, 1.0], extend_factor=1.0)
    quad2 = nurbs_quad(poles2, param_range=[0.0, 1.0, 0.0, 1.0], extend_factor=1.0)
    for j in range(num):
        u1, v1 = quad1.parameter(pts1[j])
        u2, v2 = quad2.parameter(pts2[j])
        d = FreeCAD.Vector(u1, v1).distanceToPoint(FreeCAD.Vector(u2, v2))
        print(d)
        score += d
    return score


def get_offset(sh1, f1, w1, sh2, f2, w2):
    num = len(w1.Vertexes)
    best_offset = None
    best_score = 1e50
    for i in range(-num, num):
        sc = get_poly_data(sh1, f1, w1, sh2, f2, w2, i)
        print(f"Offset {i} : Deviation score : {sc}")
        if best_score > sc:
            best_score = sc
            best_offset = i
    return best_offset


def midrange(u0, u1):
    return 0.5 * (u0 + u1)


def midrange_normal(face):
    u0, u1, v0, v1 = face.ParameterRange
    return face.normalAt(midrange(u0, u1), midrange(v0, v1))


class MatchFaces:

    def __init__(self, face1, face2):
        self.face1 = face1.copy()
        self.face2 = face2.copy()

    def transform_matrices(self):
        "Returns the LCS matrices of the 2 faces"
        cog1 = self.face1.CenterOfGravity
        u, v = self.face1.Surface.parameter(cog1)
        norm1 = self.face1.normalAt(u, v)
        pl1 = Part.Plane(cog1, norm1)

        cog2 = self.face2.CenterOfGravity
        u, v = self.face2.Surface.parameter(cog2)
        norm2 = -self.face2.normalAt(u, v)
        pl2 = Part.Plane(cog2, norm2)

        inter = pl1.intersectSS(pl2)
        if len(inter) > 0:
            yaxis = inter[0].Direction
        else:
            yaxis = pl1.uIso(0.0).tangent(0.0)[0]
        xaxis1 = yaxis.cross(norm1)
        xaxis2 = yaxis.cross(norm2)
        m1 = FreeCAD.Matrix(xaxis1, yaxis, norm1, cog1)
        m2 = FreeCAD.Matrix(xaxis2, yaxis, norm2, cog2)
        return m1, m2

    def normalize_faces(self):
        m1, m2 = self.transform_matrices()
        self.face1 = self.face1.transformShape(m1.inverse())
        dl1 = self.face1.BoundBox.DiagonalLength
        self.face1.scale(1 / dl1)
        self.face2 = self.face2.transformShape(m2.inverse())
        dl2 = self.face2.BoundBox.DiagonalLength
        self.face2.scale(1 / dl2)

    def get_wire_pairs(self):
        wl1 = self.face1.Wires
        wl2 = self.face2.Wires
        if (len(wl1) > 2) or (len(wl2) > 2):
            # TODO Eventually add a Wire Sorter
            print("BlendSolid: Warning, matching wires not yet implemented")
        wire_pairs = zip(wl1, wl2)
        return wire_pairs

    def edge_midpoint(self, e):
        p = 0.5 * (e.FirstParameter + e.LastParameter)
        return e.valueAt(p)

    def wire_offset(self, w1, w2):
        if len(w1.Edges) == 1:
            return 0, 1
        max_offset = len(w2.Edges)
        dl = []
        for off in range(max_offset):
            d = 0
            for idx in range(len(w1.OrderedEdges)):
                p1 = self.edge_midpoint(w1.OrderedEdges[idx])
                p2 = self.edge_midpoint(w2.OrderedEdges[(idx + off) % max_offset])
                d += p1.distanceToPoint(p2)
            dl.append(d)
            d = 0
            for idx in range(len(w1.OrderedEdges)):
                p1 = self.edge_midpoint(w1.OrderedEdges[idx])
                p2 = self.edge_midpoint(w2.OrderedEdges[(-idx + off) % max_offset])
                d += p1.distanceToPoint(p2)
            dl.append(d)
        for d in dl:
            print(d)
        mini = min(dl)
        maxi = max(dl)
        fid = dl.index(mini)
        offset = int(fid / 2)
        if fid % 2 == 0:
            inc = 1
        else:
            inc = -1
        dl.pop(fid)
        second = min(dl)
        ratio = (second - mini) / (maxi - mini)
        score = int(ratio * 100)
        # print(f"Blendsolid: Edge matching score = {score}%")
        return offset, inc


class BlendSolid:
    """Creates a solid shape that smoothly interpolate the faces of 2 other solids"""

    def __init__(self, f1, f2, sh1=None, sh2=None):
        self.face1 = f1
        self.face2 = f2
        self.shape1 = sh1
        self.shape2 = sh2
        self.cont1 = 2
        self.cont2 = 2
        self.surflist = []
        self.offset = []

    def get_wire_pairs(self):
        # TODO Eventually add a Wire Sorter
        wl1 = self.face1.Wires
        wl2 = self.face2.Wires
        if (len(wl1) > 2) or (len(wl2) > 2):
            print("BlendSolid: Warning, matching wires not yet implemented")
        wire_pairs = zip(wl1, wl2)
        # print(wire_pairs)
        return wire_pairs

    def build_surfaces(self):
        self.surflist = []
        mf = MatchFaces(self.face1, self.face2)
        mf.normalize_faces()
        # Part.show(mf.face1)
        # Part.show(mf.face2)
        wire_pairs = list(self.get_wire_pairs())
        for idx, tup in enumerate(wire_pairs):
            # print(f"wire pair {idx}")
            offset, inc = mf.wire_offset(*tup)
            for i in range(len(tup[0].OrderedEdges)):
                j = (inc * i + offset) % len(tup[0].OrderedEdges)
                e1 = wire_pairs[idx][0].OrderedEdges[i]
                e2 = wire_pairs[idx][1].OrderedEdges[j]
                # print(e1, e2)
                of1 = other_face(self.shape1, self.face1, e1)
                of2 = other_face(self.shape2, self.face2, e2)
                bs = bc.BlendSurface(e1, of1, e2, of2)
                # print(e1, of1, e2, of2)
                self.surflist.append(bs)
        # print("build surface OK")

    def surfaces(self):
        if not len(self.surflist) == min(len(self.face1.Edges), len(self.face2.Edges)):
            self.build_surfaces()
        return self.surflist

    @property
    def Surfaces(self):
        sl = []
        for surf in self.surfaces():
            sl.append(surf.surface)
        return sl

    @property
    def Faces(self):
        fl = []
        for surf in self.surfaces():
            fl.append(surf.face)
        return fl

    @property
    def Shape(self):
        shape = Part.Compound(self.Faces + [self.face1, self.face2])
        try:
            shell = Part.makeShell(shape.Faces)
            if shell.isValid():
                shape = shell
        except Part.OCCError:
            pass
        try:
            solid = Part.Solid(shape)
            if solid.isValid():
                shape = solid
        except Part.OCCError:
            pass
        return shape

    def minimize_curvature(self, num=3):
        for surf in self.surfaces():
            surf.minimize_curvature(num)

    def auto_scale(self, num=3):
        for surf in self.surfaces():
            # print("surf.auto_scale")
            surf.auto_scale(num)

    def set_size(self, sc1, sc2):
        for surf in self.surfaces():
            surf.edge1.size = sc1
            surf.edge2.size = sc2

    def set_continuity(self, c):
        for surf in self.surfaces():
            surf.continuity = c

    def update_surfaces(self, num=20):
        for surf in self.surfaces():
            surf.perform(num)

    def match_shapes(self, sl1, sl2):
        off = []
        for i, tup in enumerate(self.get_wire_pairs()):
            # print(f"Wire{i + 1}")
            sorter = MatchWires(*tup)
            off.append(sorter.connect_subshapes(sl1, sl2))
        if len(off) == i + 1:
            self.offset = off
            # print(off)
        self.build_surfaces()

