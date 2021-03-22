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


class BoundarySorter:
    def __init__(self, wires, surface=None, only_closed=False):
        self.wires = []
        self.parents = []
        self.sorted_wires = []
        self.surface = surface
        for w in wires:
            if only_closed and not w.isClosed():
                print("Skipping open wire")
                continue
            self.wires.append(w)
            self.parents.append([])
            self.sorted_wires.append([])
        self.done = False

    def fine_check_inside(self, w1, w2):
        if self.surface is not None:
            f = Part.Face(self.surface, w2)
        else:
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


class FaceWrapper:
    """Wrap shapes on a face"""
    def __init__(self, face, quad):
        self.face = face
        self.quad = quad
        self.faces = []
        self.wires = []
        self.edges = []
        self.offset = 0.0
        self.extrusion = 0.0
        self.fill_faces = True
        self.fill_extrusion = True

    def force_closed_bspline2d(self, c2d):
        """Force close a 2D Bspline curve by moving last pole to first"""
        c2d.setPole(c2d.NbPoles, c2d.getPole(1))
        print("Force closing 2D curve")

    def build_faces(self, wl, face):
        faces = []
        for w in wl:
            w.fixWire(face, 1e-7)
        bs = BoundarySorter(wl, face.Surface, True)
        for i, wirelist in enumerate(bs.sort()):
            # print(wirelist)
            f = Part.Face(face.Surface, wirelist[0])
            try:
                f.check()
            except Exception as e:
                print(str(e))
            if not f.isValid():
                f.validate()
                if not f.isValid():
                    print("Validating plain face{:3} failed".format(i))
            if len(wirelist) > 1:
                try:
                    f.cutHoles(wirelist[1:])
                    f.validate()
                except AttributeError:
                    print("Faces with holes require FC 0.19 or higher\nIgnoring holes\n")
            f.sewShape()
            if not f.isValid():
                print("Invalid final face{:3}".format(i))
            faces.append(f)
        return faces

    def wrap_shapes(self, shapes):
        for sh in shapes:
            for face in sh.Faces:
                if self.fill_faces:
                    self.map_shape(face)
                else:
                    self.map_shapes(face.Wires)
            for wire in sh.Wires:
                if sh.ancestorsOfType(wire, Part.Face) == []:
                    self.map_shape(wire)
            for edge in sh.Edges:
                if sh.ancestorsOfType(edge, Part.Wire) == []:
                    self.map_shape(edge)

    def wrap_shape(self, shape):
        if not isinstance(shape, Part.Shape):
            return []
        proj_edges = []
        for oe in shape.Edges:
            # debug("original edge has : {} Pcurves : {}".format(_utils.nb_pcurves(oe), oe.curveOnSurface(0)))
            proj_edges.extend(self.quad.project(oe).Edges)
        
            for e in proj.Edges:
                # debug("edge on quad has : {} Pcurves : {}".format(_utils.nb_pcurves(e), e.curveOnSurface(0)))
                c2d, fp, lp = self.quad.curveOnSurface(e)
                if oe.isClosed() and not c2d.isClosed():
                    self.force_closed_bspline2d(c2d)
                ne = c2d.toShape(self.face.Surface, fp, lp)
                # debug("edge on face has : {} Pcurves : {}".format(_utils.nb_pcurves(ne), ne.curveOnSurface(0)))
                # debug(ne.Placement)
                # debug(face.Placement)
                # ne.Placement = face.Placement
                vt = ne.getTolerance(1, Part.Vertex)
                et = ne.getTolerance(1, Part.Edge)
                if vt < et:
                    ne.fixTolerance(et, Part.Vertex)
                    print("fixing Vertex tolerance : {0:e} -> {1:e}".format(vt, et))
                new_edges.append(ne)
            # else: # except TypeError:
                # error("Failed to get 2D curve")
        sorted_edges = Part.sortEdges(new_edges)
        wirelist = [Part.Wire(el) for el in sorted_edges]
        if self.fill_faces:
            return self.build_faces(wirelist, self.face)
        else:
            return wirelist

    def execute(self, fp):
        quad = fp.FaceMap.Shape.Face1.Surface.toShape()
        face = fp.FaceMap.Proxy.get_face(fp.FaceMap)
        imput_shapes = [o.Shape for o in fp.Sources]
        shapes_1 = []
        shapes_2 = []
        if (fp.Offset == 0):
            shapes_1 = self.map_shapelist(imput_shapes, quad, face, fp.FillFaces)
        else:
            f1 = face.makeOffsetShape(fp.Offset, 1e-7)
            shapes_1 = self.map_shapelist(imput_shapes, quad, f1.Face1, fp.FillFaces)
        if (fp.Thickness == 0):
            if shapes_1:
                fp.Shape = Part.Compound(shapes_1)
            return
        else:
            f2 = face.makeOffsetShape(fp.Offset + fp.Thickness, 1e-7)
            shapes_2 = self.map_shapelist(imput_shapes, quad, f2.Face1, fp.FillFaces)
            if not fp.FillExtrusion:
                if shapes_1 or shapes_2:
                    fp.Shape = Part.Compound(shapes_1 + shapes_2)
                    return
            else:
                shapes = []
                for i in range(len(shapes_1)):
                    if isinstance(shapes_1[i], Part.Face):
                        faces = shapes_1[i].Faces + shapes_2[i].Faces
                        # error_wires = []
                        for j in range(len(shapes_1[i].Edges)):
                            if fp.FillFaces and shapes_1[i].Edges[j].isSeam(shapes_1[i]):
                                continue
                            ruled = Part.makeRuledSurface(shapes_1[i].Edges[j], shapes_2[i].Edges[j])
                            ruled.check(True)
                            faces.append(ruled)
                        try:
                            shell = Part.Shell(faces)
                            shell.sewShape()
                            # print_tolerance(shell)
                            solid = Part.Solid(shell)
                            solid.fixTolerance(1e-5)
                            shapes.append(solid)
                        except Exception:
                            FreeCAD.Console.PrintWarning("Sketch on surface : failed to create solid # {}.\n".format(i + 1))
                            shapes.extend(faces)
                    else:
                        ruled = Part.makeRuledSurface(shapes_1[i].Wires[0], shapes_2[i].Wires[0])
                        ruled.check(True)
                        shapes.append(ruled)
                # shapes.append(quad)
                if shapes:
                    if len(shapes) == 1:
                        fp.Shape = shapes[0]
                    elif len(shapes) > 1:
                        fp.Shape = Part.Compound(shapes)
