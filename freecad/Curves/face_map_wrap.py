# -*- coding: utf-8 -*-

__title__ = "FaceMapper"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Create a flat map of a face"""

import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves.nurbs_tools import nurbs_quad

vec2 = FreeCAD.Base.Vector2d


def build_face_with_holes(outer_wire, inner_wires=[], surface=None):
    """Build a face on a surface, from an outer wire(boundary),
    and a list of inner wires(holes)"""
    try:
        if surface is not None:
            f = Part.Face(surface, outer_wire)
        else:
            f = Part.Face(outer_wire)
        f.validate()
    except Part.OCCError:
        return Part.Wire()
    if not hasattr(f, "cutHoles"):
        print("Faces with holes require FC 0.19 or higher\nIgnoring holes\n")
    if not f.isValid():
        print("Validating plain face failed")
    if len(inner_wires) > 0:
        f.cutHoles(inner_wires)
        f.validate()
    f.sewShape()
    if not f.isValid():
        print("Invalid final face")
    return f


class BoundarySorter:
    """Sorts a list of nested wires.
    b_sorter = BoundarySorter(wires, only_closed=True)
    If only_closed is True, open wires will be ignored.
    b_sorter.sort() returns a list of lists of wires
    b_sorter.faces() returns a list of faces"""
    def __init__(self, wires, only_closed=True):
        self.wires = []
        self.parents = []
        self.sorted_wires = []
        for w in wires:
            if only_closed and not w.isClosed():
                print("Skipping open wire")
                continue
            self.wires.append(w)
            self.parents.append([])
            self.sorted_wires.append([])
        self.done = False

    def fine_check_inside(self, w1, w2):
        f = Part.Face(w2)
        if not f.isValid():
            f.validate()
        if f.isValid():
            pt = w1.Vertex1.Point
            u, v = f.Surface.parameter(pt)
            return f.isPartOfDomain(u, v)
        return False

    def check_inside(self):
        for i, w1 in enumerate(self.wires):
            for j, w2 in enumerate(self.wires):
                if not i == j:
                    if w2.BoundBox.isInside(w1.BoundBox):
                        if self.fine_check_inside(w1, w2):
                            self.parents[i].append(j)

    def sort_pass(self):
        to_remove = []
        for i, p in enumerate(self.parents):
            if (p is not None) and p == []:
                to_remove.append(i)
                self.sorted_wires[i].append(self.wires[i])
                self.parents[i] = None
        for i, p in enumerate(self.parents):
            if (p is not None) and len(p) == 1:
                to_remove.append(i)
                self.sorted_wires[p[0]].append(self.wires[i])
                self.parents[i] = None
        # print("Removing full : {}".format(to_remove))
        if len(to_remove) > 0:
            for i, p in enumerate(self.parents):
                if (p is not None):
                    for r in to_remove:
                        if r in p:
                            p.remove(r)
        else:
            self.done = True

    def sort(self):
        self.check_inside()
        # print(self.parents)
        while not self.done:
            # print("Pass {}".format(i))
            self.sort_pass()
        result = []
        for w in self.sorted_wires:
            if w:
                result.append(w)
        return result

    def faces(self):
        faces = []
        for i, wl in enumerate(self.sort()):
            # print(wl)
            f = build_face_with_holes(wl[0], wl[1:])
            if f.isValid():
                faces.append(f)
            else:
                print("Invalid final face{:3}".format(i))
        return faces


class FaceMapper:
    """Create a flat map of a face"""
    def __init__(self, face):
        self.face = face
        self._quad = None

    @property
    def quad(self):
        if self._quad is None:
            self.set_quad()
        return self._quad

    def boundbox_2d(self):
        u0, u1, v0, v1 = self.face.ParameterRange
        line_top = Part.Geom2d.Line2dSegment(vec2(u0, v1), vec2(u1, v1))
        line_bottom = Part.Geom2d.Line2dSegment(vec2(u0, v0), vec2(u1, v0))
        line_right = Part.Geom2d.Line2dSegment(vec2(u0, v0), vec2(u0, v1))
        line_left = Part.Geom2d.Line2dSegment(vec2(u1, v0), vec2(u1, v1))
        return line_bottom, line_top, line_left, line_right

    def boundbox_3d(self, target_surface):
        edges = [e.toShape(target_surface) for e in self.boundbox_2d()]
        return Part.Wire(Part.sortEdges(edges)[0])

    def boundbox_on_face(self):
        return self.boundbox_3d(self.face.Surface)

    def boundbox_flat(self):
        return self.boundbox_3d(self.quad)

    def set_quad(self, sizeU=1.0, sizeV=1.0, extend_factor=1.0):
        poles = [[FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, sizeV, 0)],
                 [FreeCAD.Vector(sizeU, 0, 0), FreeCAD.Vector(sizeU, sizeV, 0)]]
        self._quad = nurbs_quad(poles, self.face.ParameterRange, extend_factor)
        return self._quad

    def reverseU(self, b=False):
        if b:
            pts = self.quad.getPoles()
            self.quad.setPoleRow(1, pts[1])
            self.quad.setPoleRow(2, pts[0])

    def reverseV(self, b=False):
        if b:
            pts = list(zip(*self.quad.getPoles()))
            self.quad.setPoleCol(1, pts[1])
            self.quad.setPoleCol(2, pts[0])

    def swapUV(self, b=False):
        if b:
            self.quad.exchangeUV()
            # pts = list(zip(*self.quad.getPoles()))
            # self.quad.setPoleRow(1, pts[0])
            # self.quad.setPoleRow(2, pts[1])

    def face_flatmap(self, fill_face=False):
        outer_wire = None
        inner_wires = []
        for w in self.face.Wires:
            el = []
            for e in w.Edges:
                cos, fp, lp = self.face.curveOnSurface(e)
                el.append(cos.toShape(self.quad, fp, lp))
                if e.isSeam(self.face):
                    e.reverse()
                    cos, fp, lp = self.face.curveOnSurface(e)
                    el.append(cos.toShape(self.quad, fp, lp))
            flat_wire = Part.Wire(Part.sortEdges(el)[0])
            if w.isSame(self.face.OuterWire):
                outer_wire = flat_wire
            else:
                inner_wires.append(flat_wire)
        # build a face, or a compound of wires
        if fill_face:
            mapface = Part.Face(self.quad, outer_wire)
            if inner_wires:
                mapface.validate()
                mapface.cutHoles(inner_wires)
            mapface.validate()
        else:
            mapface = Part.Compound([outer_wire] + inner_wires)
        return mapface


def wrap_on_face(shape, face, quad):
    """Wrap a shape(face, wire, or edge) on a face,
    using quad as the flat transfer face.
    Returns a face or a wire
    wrapped_shape = wrap_on_face(shape, face, quad)"""
    if isinstance(shape, Part.Face):
        ow = wrap_on_face(shape.OuterWire, face, quad)
        iw = [wrap_on_face(w, face, quad) for w in shape.Wires if not w.isSame(shape.OuterWire)]
        return build_face_with_holes(ow, iw, face.Surface)
    elif isinstance(shape, Part.Wire):
        edges = []
        for e in shape.OrderedEdges:
            edges.extend(wrap_on_face(e, face, quad).Edges)
        # print(edges)
        se = Part.sortEdges(edges)
        if se:
            return Part.Wire(Part.sortEdges(edges)[0])
    elif isinstance(shape, Part.Edge):
        new_edges = []
        for e in quad.project([shape]).Edges:
            c2d, fp, lp = quad.curveOnSurface(e)
            if shape.isClosed() and not c2d.isClosed():
                c2d.setPole(c2d.NbPoles, c2d.getPole(1))
            new_edges += c2d.toShape(face.Surface, fp, lp).Edges
        if len(new_edges) >= 1:
            return Part.Wire(Part.sortEdges(new_edges)[0])
    return Part.Wire()


class ShapeWrapper:
    """Wrap shapes on a face"""
    def __init__(self, face, quad):
        self.face = face
        self.quad = quad
        self.offset = 0.0
        self.extrusion = 0.0
        self.fill_faces = True
        self.fill_extrusion = True

    @property
    def extrude(self):
        return not (self.extrusion == 0.0)

    def decompose(self, in_shapes):
        if not isinstance(in_shapes, (list, tuple)):
            in_shapes = [in_shapes, ]
        shapelist = []
        for shape in in_shapes:
            if not isinstance(shape, (Part.Face, Part.Wire, Part.Edge)):
                for f in shape.Faces:
                    shapelist.append(f)
                for wire in shape.Wires:
                    if shape.ancestorsOfType(wire, Part.Face) == []:
                        shapelist.append(wire)
                for edge in shape.Edges:
                    if shape.ancestorsOfType(edge, Part.Wire) == []:
                        shapelist.append(edge)
            else:
                shapelist.append(shape)
        return shapelist

    def wrap(self, in_shapes):
        shapelist = self.decompose(in_shapes)
        shapes_1 = []
        shapes_2 = []
        if self.offset == 0.0:
            self.face1 = self.face
        else:
            self.face1 = self.face.makeOffsetShape(self.offset, 1e-7).Face1
        shapes_1 = [wrap_on_face(sh, self.face1, self.quad) for sh in shapelist]
        if not self.extrude:
            return Part.Compound(shapes_1)

        self.face2 = self.face.makeOffsetShape(self.offset + self.extrusion, 1e-7).Face1
        shapes_2 = [wrap_on_face(sh, self.face2, self.quad) for sh in shapelist]
        if not self.fill_extrusion:
            return Part.Compound(shapes_1 + shapes_2)

        shapes = []
        for i in range(len(shapes_1)):
            if isinstance(shapes_1[i], Part.Face):
                faces = []
                if self.fill_faces:
                    faces = shapes_1[i].Faces + shapes_2[i].Faces
                    # error_wires = []
                for j in range(len(shapes_1[i].Edges)):
                    if self.fill_faces and shapes_1[i].Edges[j].isSeam(shapes_1[i]):
                        continue
                    ruled = Part.makeRuledSurface(shapes_1[i].Edges[j], shapes_2[i].Edges[j])
                    # ruled.check(True)
                    faces.append(ruled)
                try:
                    shell = Part.makeShell(faces)
                    shell.sewShape()
                    # print_tolerance(shell)
                    solid = Part.makeSolid(shell)
                    # solid.fixTolerance(1e-5)
                    shapes.append(solid)
                except Exception:
                    FreeCAD.Console.PrintWarning("Sketch on surface : failed to create solid # {}.\n".format(i + 1))
                    shapes.extend(faces)
            else:
                if shapes_1[i].Wires and shapes_2[i].Wires:
                    ruled = Part.makeRuledSurface(shapes_1[i].Wires[0], shapes_2[i].Wires[0])
                    # ruled.check(True)
                    shapes.append(ruled)
        if len(shapes) == 1:
            return shapes[0]
        elif len(shapes) > 1:
            return Part.Compound(shapes)
        return Part.Shape()
