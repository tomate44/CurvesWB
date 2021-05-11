import FreeCAD
import FreeCADGui
import Part
from . import _utils
from . import blend_curve as bc
from .nurbs_tools import nurbs_quad
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
    print(e)
    anc = sh.ancestorsOfType(e, Part.Face)
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


class MatchWires:
    """Find the best vertex connections between two wires"""
    def __init__(self, w1, w2):
        self.w1 = w1
        self.w2 = w2
        self.el1 = self.w1.OrderedEdges
        self.el2 = self.w2.OrderedEdges
        # self.el3 = self.reverse_list(self.w2.OrderedEdges)
        self.dir1 = None
        self.dir2 = None
        self.sh1 = None
        self.sh2 = None
        self.nb_edges = min(len(w1.Edges), len(w2.Edges))
        self.offset = 0
        self.reverse = False

    def Edges(self):
        for idx1 in range(self.nb_edges):
            idx2 = self.offset_index(idx1)
            # print(f"Edges {idx1}-{idx2}")
            yield(self.w1.OrderedEdges[idx1], self.w2.OrderedEdges[idx2])

    def offset_index(self, i):
        if self.reverse:
            return (self.nb_edges - i + abs(self.offset)) % self.nb_edges
        else:
            return (i + abs(self.offset)) % self.nb_edges

    #def ov_idx(self, pair):
        #i1 = False
        #i2 = False
        #v1, v2 = pair
        #for i, ov1 in enumerate(self.w1.OrderedVertexes):
            #if ov1.isSame(v1) or ov1.isSame(v2):
                #i1 = i
        #for j, ov2 in enumerate(self.w2.OrderedVertexes):
            #if ov2.isSame(v1) or ov2.isSame(v2):
                #i2 = j
        #return i1, i2

    def reverse_list(self, li):
        nl = li[::-1]
        return nl[-1:] + nl[:-1]

    def offset_list(self, li, n):
        return li[n:] + li[:n]

    def find_idx(self, shapes, li):
        for s in shapes:
            for i, o in enumerate(li):
                if o.isSame(s):
                    return i

    def edge_idx(self, pair):
        i1 = self.find_idx(pair, self.el1)
        i2 = self.find_idx(pair, self.el2)
        # i3 = self.find_idx(pair, self.el3)
        return i1, i2  # , i3

    def calc_offset(self, i, j):
        off = j - i
        if off < 0:
            off = off + self.nb_edges - 1
        return off

    def connect_subshapes(self, pairs):
        for pair in pairs:
            i1, i2 = self.edge_idx(pair)
            off = self.calc_offset(i1, i2)
            if self.offset is False:
                self.offset = off
                self.el1 = self.offset_list(self.el1, self.offset)
                self.el2 = self.offset_list(self.el2, self.offset)
                print(f"Setting Offset : {self.offset}")
            else:
                print(f"Reverse Offset : {off}")
                if i1 == i2:
                    print("Forward offset")
                    return self.offset
                else:
                    print("Reverse offset")
                    return -self.offset

    def connect_subshapes_old(self, pairs):
        _tmp = 0, 0
        for pair in pairs:
            i1, i2, i3 = self.edge_idx(pair)
            forward, reverse = self.calc_offset(i1, i2), self.calc_offset(i1, i3)
            if forward == 0:
                self.reverse = False
                print(f"Forward offset = {_tmp[0]}")
            elif reverse == 0:
                self.reverse = True
                print(f"Reverse offset = {_tmp[1]}")
            else:
                self.el2 = self.offset_list(self.el2, forward)
                self.el3 = self.offset_list(self.el3, reverse)
                print(f"Setting Offset : {forward}, {reverse}")
                _tmp = forward, reverse
        if self.reverse:
            self.offset = _tmp[1]
            return -self.offset
        else:
            self.offset = _tmp[0]
            return self.offset

    @staticmethod
    def other_edge(sh, fw, v):
        if sh:
            sh_anc = sh.ancestorsOfType(v, Part.Edge)
            fw_anc = fw.ancestorsOfType(v, Part.Edge)
            for e1 in sh_anc:
                found = False
                for e2 in fw_anc:
                    if e1.isPartner(e2):
                        found = True
                if not found:  # e1 doesn't belong to face
                    return e1
        return False

    @staticmethod
    def external_line(sh, fw, v):
        line = Part.Line()
        line.Location = v.Point
        e = other_edge(sh, fw, v)
        if e:
            p = e.Curve.parameter(v.Point)
            fp = e.Curve.FirstParameter
            lp = e.Curve.LastParameter
            if abs(p - fp) > abs(p - lp):
                line.Direction = e.Curve.tangent(p)[0]
            else:
                line.Direction = -e.Curve.tangent(p)[0]
            return line
        if isinstance(fw, Part.Face):
            line.Direction = midrange_normal(fw)
            return line

    def normalized_ptcloud(self, vl, e, xdir):
        o = e.Curve.Location
        n = e.Curve.Direction
        plane = Part.Plane(o, o + xdir, o + xdir.cross(n))
        pars = [plane.parameter(v.Point) for v in vl]
        pts = [plane.value(u,v) for u,v in pars]
        # print(pts)
        poly = Part.makePolygon(pts)
        bb = poly.BoundBox
        norm_pts = []
        for p in pts:
            norm_pts.append(FreeCAD.Vector(p.x / bb.XLength, p.y / bb.YLength, 0))
        Part.show(Part.makePolygon(norm_pts))
        return norm_pts

    def morphing_score(self, idx, off):
        idx2 = self.offset_index(idx, off)
        v1 = self.w1.OrderedVertexes[idx]
        v2 = self.w2.OrderedVertexes[idx2]
        e1 = self.external_line(self.sh1, self.w1, v1).toShape(0, 1e20)
        e2 = self.external_line(self.sh2, self.w2, v2).toShape(0, 1e20)
        d, pts, info = e1.distToShape(e2)
        print(pts)
        pts1 = self.normalized_ptcloud(self.w1.OrderedVertexes, e1, pts[0][1] - pts[0][0])
        vl = [self.w2.OrderedVertexes[self.offset_index(i, off)] for i in range(self.nb_edges)]
        pts2 = self.normalized_ptcloud(vl, e2, pts[0][0] - pts[0][1])
        score = 0
        for i in range(len(pts1)):
            score += pts1[i].distanceToPoint(pts2[i])
        print(f"Morphing score({off}) = {score}")
        return score

    def find_best_offset(self):
        offset_list = [self.morphing_score(0, i) for i in range(-self.nb_edges, self.nb_edges)]
        self.offset = offset_list.index(min(offset_list))
        return self.offset


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
        wire_pairs = zip(wl1, wl2)
        return wire_pairs

    def build_surfaces(self):
        self.surflist = []
        for idx, tup in enumerate(self.get_wire_pairs()):
            sorter = MatchWires(*tup)
            if idx < len(self.offset):
                sorter.offset = abs(self.offset[idx])
                sorter.reverse = self.offset[idx] < 0
            for e1, e2 in sorter.Edges():
                of1 = other_face(self.shape1, self.face1, e1)
                of2 = other_face(self.shape2, self.face2, e2)
                bs = bc.BlendSurface(e1, of1, e2, of2)
                # bs.edge1.angle = (90, 80, 100, 90)
                # bs.edge2.angle = (90, 90, 90, 70)
                bs.continuity = self.cont1, self.cont2
                self.surflist.append(bs)

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
            surf.auto_scale(num)

    def set_size(self, sc1, sc2):
        for surf in self.surfaces():
            surf.edge1.size = sc1
            surf.edge2.size = sc2

    def update_surfaces(self, num=20):
        for surf in self.surfaces():
            surf.perform(num)

    def match_shapes(self, pairs):
        off = []
        for i, tup in enumerate(self.get_wire_pairs()):
            print(f"Wire{i + 1}")
            sorter = MatchWires(*tup)
            off.append(sorter.connect_subshapes(pairs))
        if len(off) == i + 1:
            self.offset = off
            print(off)
        self.build_surfaces()


def test():
    cont1 = 3
    cont2 = 3
    num = 21

    edges = []
    faces = []

    sel = FreeCADGui.Selection.getSelectionEx()
    s = get_selection_data(sel)
    sh1, f1, v1 = s[0]
    sh2, f2, v2 = s[1]


    for w1, w2 in zip(f1.Wires, f2.Wires):
        for e1, e2 in zip(w1.Edges, w2.Edges):
            of1 = other_face(sh1, f1, e1)
            of2 = other_face(sh2, f2, e2)
            bs = bc.BlendSurface(e1, of1, e2, of2)
            # bs.edge1.angle = (90, 80, 100, 90)
            # bs.edge2.angle = (90, 90, 90, 70)
            bs.continuity = 3
            # bs.minimize_curvature()
            bs.auto_scale()
            bs.perform(num)
            edges.extend(bs.edges.Edges)
            faces.append(bs.face)
            Part.show(Part.Compound(bs.edges.Edges + [bs.face]))

    # Part.show(Part.Compound(edges + faces))

