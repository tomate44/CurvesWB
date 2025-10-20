# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part


DEBUG = True


def debug(message):
    if DEBUG:
        FreeCAD.Console.PrintMessage(message + "\n")


def stretched_plane(poles, param_range=[0, 2, 0, 2], extend_factor=1.0):
    s0, s1, t0, t1 = param_range
    bs = Part.BSplineSurface()
    umults = [2, 2]
    vmults = [2, 2]
    uknots = [s0, s1]
    vknots = [t0, t1]
    if extend_factor > 1.0:
        ur = s1 - s0
        vr = t1 - t0
        uknots = [s0 - extend_factor * ur, s1 + extend_factor * ur]
        vknots = [t0 - extend_factor * vr, t1 + extend_factor * vr]
        diag_1 = poles[1][1] - poles[0][0]
        diag_2 = poles[1][0] - poles[0][1]
        np1 = poles[0][0] - extend_factor * diag_1
        np2 = poles[0][1] - extend_factor * diag_2
        np3 = poles[1][0] + extend_factor * diag_2
        np4 = poles[1][1] + extend_factor * diag_1
        poles = [[np1, np2], [np3, np4]]
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                False, False, 1, 1)
    return bs


class Quad:
    def __init__(self, bounds=None):
        self.quad = Part.BSplineSurface()
        if bounds is not None:
            self.Limits = bounds

    @property
    def Face(self):
        return self.quad.toShape()

    @property
    def Surface(self):
        return self.quad

    @property
    def Limits(self):
        pu1, pu2 = self.quad.getPoles()
        p00 = pu1[0]
        p11 = pu2[-1]
        return p00.x, p11.x, p00.y, p11.y

    @Limits.setter
    def Limits(self, bounds):
        if not (len(bounds) == 4):
            raise RuntimeError("Quad need 4 bounds")
        u0, u1, v0, v1 = bounds
        self.quad.setPole(1, 1, FreeCAD.Vector(u0, v0, 0))
        self.quad.setPole(1, 2, FreeCAD.Vector(u0, v1, 0))
        self.quad.setPole(2, 1, FreeCAD.Vector(u1, v0, 0))
        self.quad.setPole(2, 2, FreeCAD.Vector(u1, v1, 0))

    @property
    def Bounds(self):
        return self.quad.bounds()

    @Bounds.setter
    def Bounds(self, bounds):
        if not (len(bounds) == 4):
            raise RuntimeError("Quad need 4 bounds")
        self.quad.setUKnot(1, bounds[0])
        self.quad.setUKnot(2, bounds[1])
        self.quad.setVKnot(1, bounds[2])
        self.quad.setVKnot(2, bounds[3])
        # self.quad.scaleKnotsToBounds(*bounds) is less precise

    def extend(self, *bounds):
        u0, u1, v0, v1 = self.Limits
        if len(bounds) == 1:
            s0 = u0 - bounds[0]
            s1 = u1 + bounds[0]
            t0 = v0 - bounds[0]
            t1 = v1 + bounds[0]
        elif len(bounds) == 2:
            s0 = u0 - bounds[0]
            s1 = u1 + bounds[0]
            t0 = v0 - bounds[1]
            t1 = v1 + bounds[1]
        elif len(bounds) == 4:
            s0, s1, t0, t1 = bounds
        else:
            raise RuntimeError("Quad.extend need 1,2 or 4 parameters")
        ku0, ku1, kv0, kv1 = self.Bounds
        nu0, nu1, nv0, nv1 = self.Bounds
        if s0 < u0:
            nu0 += (ku1 - ku0) * (s0 - u0) / (u1 - u0)
        if s1 > u1:
            nu1 += (ku1 - ku0) * (s1 - u1) / (u1 - u0)
        if t0 < v0:
            nv0 += (kv1 - kv0) * (t0 - v0) / (v1 - v0)
        if t1 > v1:
            nv1 += (kv1 - kv0) * (t1 - v1) / (v1 - v0)
        self.Limits = s0, s1, t0, t1
        self.Bounds = nu0, nu1, nv0, nv1

    def reverseU(self):
        u1, u2 = self.quad.getPoles()
        self.quad.setPole(1, 1, u2[0])
        self.quad.setPole(1, 2, u2[1])
        self.quad.setPole(2, 1, u1[0])
        self.quad.setPole(2, 2, u1[1])

    def reverseV(self):
        u1, u2 = self.quad.getPoles()
        self.quad.setPole(1, 1, u1[1])
        self.quad.setPole(1, 2, u1[0])
        self.quad.setPole(2, 1, u2[1])
        self.quad.setPole(2, 2, u2[0])

    def swapUV(self):
        u1, u2 = self.quad.getPoles()
        self.quad.setPole(1, 1, u2[1])
        self.quad.setPole(1, 2, u2[0])
        self.quad.setPole(2, 1, u1[1])
        self.quad.setPole(2, 2, u1[0])


class ShapeMapper:
    """Transfer shapes (faces, wires, edges, vertexes)
    on a target surface.
    """

    def __init__(self, target, transfer):
        self.Target = target
        self.Transfer = transfer

    def project(self, shapes):
        proj = self.Transfer.project(shapes)
        return proj  # Compound of edges

    def find_seam(self, cos, tol=1e-7):
        pc, fp, lp = cos
        surf = self.Transfer.Surface
        u0, u1, v0, v1 = surf.bounds()
        if surf.isUClosed():
            if self.touch_u(cos, u0, tol):
                debug(f"Pcurve is on U0={u0:3.3f} seam")
                pc2 = pc.copy()
                pc2.translate(FreeCAD.Base.Vector2d(u1 - u0, 0))
                # pc2.reverse()
                return pc2, fp, lp
            if self.touch_u(cos, u1, tol):
                debug(f"Pcurve is on U1={u1:3.3f} seam")
                pc2 = pc.copy()
                pc2.translate(FreeCAD.Base.Vector2d(u0 - u1, 0))
                # pc2.reverse()
                return pc2, fp, lp
        if surf.isVClosed():
            if self.touch_v(cos, v0, tol):
                debug(f"Pcurve is on V0={v0:3.3f} seam")
                pc2 = pc.copy()
                pc2.translate(FreeCAD.Base.Vector2d(0, v1 - v0))
                # pc2.reverse()
                return pc2, fp, lp
            if self.touch_v(cos, v1, tol):
                debug(f"Pcurve is on V1={v1:3.3f} seam")
                pc2 = pc.copy()
                pc2.translate(FreeCAD.Base.Vector2d(0, v0 - v1))
                # pc2.reverse()
                return pc2, fp, lp

    def touch_u(self, cos, u, tol=1e-7):
        pc, fp, lp = cos
        p1 = pc.value(fp)
        p2 = pc.value(lp)
        p3 = pc.value((fp + lp) / 2)
        err = abs(p1.x - u) + abs(p2.x - u) + abs(p3.x - u)
        if err < (3 * tol):
            return True
        return False

    def touch_v(self, cos, v, tol=1e-7):
        pc, fp, lp = cos
        p1 = pc.value(fp)
        p2 = pc.value(lp)
        p3 = pc.value((fp + lp) / 2)
        err = abs(p1.y - v) + abs(p2.y - v) + abs(p3.y - v)
        if err < (3 * tol):
            return True
        return False

    def get_pcurves(self, shapes):
        pcl = []
        for e in shapes:
            cos = self.Transfer.curveOnSurface(e)
            if len(cos) > 0:
                pcl.append(cos)
                seam = self.find_seam(cos)
                if seam is not None:
                    pcl.append(seam)
        if len(pcl) > 0:
            return pcl
        else:
            proj = self.project(shapes)
            ppcl = self.get_pcurves(proj)
            if len(ppcl) > 0:
                return ppcl

    def upgrade_shapes(self, shapes, surf=None, fixtol=True):
        if isinstance(shapes[0], Part.Edge):
            wires = []
            if surf:
                fixface = surf.toShape()
            sel = Part.sortEdges(shapes)
            if (len(sel) > 1) and fixtol:
                debug(f"Edges sorted into {len(sel)} groups")
                vertexes = Part.Compound(shapes).Vertexes
                dist_list = []
                for v1 in vertexes:
                    dist = 1e50
                    for v2 in vertexes:
                        if not v1.isSame(v2):
                            d = v1.Point.distanceToPoint(v2.Point)
                            dist = min(dist, d)
                    dist_list.append(dist)
                tol = max(dist_list) + 1e-8
                debug(f"Increasing Vertex Tolerance to {tol}")
                for e in shapes:
                    e.fixTolerance(tol, Part.Vertex)
                w = Part.Wire(shapes)
                if surf:
                    w.fixWire(fixface, tol)
                wires = [w, ]
                debug(f"Reduced to {len(wires)} groups")
            else:
                for el in sel:
                    w = Part.Wire(el)
                    if surf:
                        w.fixWire(fixface)
                    wires.append(w)
                debug(f"Upgraded {len(shapes)} edges to {len(wires)} wires")
            if len(wires) > 1:
                wires.sort(key=lambda x: x.Length)
                for w in wires[1:]:
                    w.reverse()
            return Part.Compound(wires)
        elif isinstance(shapes[0], Part.Wire):
            debug(f"Upgrading {len(shapes)} wires to face")
            # wires = sorted(shapes, key=lambda x: x.BoundBox.DiagonalLength)
            s = surf.Surface
            # s.extend(1.0)
            ff = Part.Face(s, shapes[0])
            try:
                ff.validate()
            except Part.OCCError:
                print("face validation failed")
            for w in shapes[1:]:
                print(w.Length)
                if w.Orientation == "Forward":
                    w.reverse()
                try:
                    ff.cutHoles([w])
                    ff.validate()
                except Part.OCCError:
                    print("cutHoles failed")
            if ff.isValid():
                debug("... Success")
                return ff
            debug("... Failed")
        if len(shapes) == 1:
            return shapes[0]
        return Part.Compound(shapes)

    def map_shape(self, shape, upgrade=True):
        debug(f"Map_Shape : {shape.__class__}")
        if isinstance(shape, (list, tuple)):
            shl = []
            for sh in shape:
                shl.append(self.map_shape(sh, False))
            return shl
        elif isinstance(shape, Part.Vertex):
            proj = self.Transfer.Surface.parameter(shape.Point)
            if len(proj) == 2:
                pt = self.Target.valueAt(*proj)
                return Part.Vertex(pt)
        if not upgrade or isinstance(shape, Part.Edge):
            pcurves = self.get_pcurves(shape.Edges)
            edges = []
            for pc, fp, lp in pcurves:
                me = pc.toShape(self.Target, fp, lp)
                edges.append(me)
            return Part.Compound(edges)
        if isinstance(shape, Part.Face):
            wires = []  # self.map_shape(shape.OuterWire, True).Wires
            for w in shape.Wires:
                # if not w.isSame(shape.OuterWire):
                wires.extend(self.map_shape(w, True).Wires)
            # f = Part.Face(self.Target, wires)
            # # TODO Check and repair face
            return self.upgrade_shapes(wires, self.Target)
        elif isinstance(shape, Part.Wire):
            edges = []
            for e in shape.Edges:
                edges.extend(self.map_shape(e).Edges)
            # comp = Part.Compound(edges)
            # TODO Check and repair wire
            return self.upgrade_shapes(edges)
        else:
            raise (RuntimeError, f"ShapeMapper.map_shape : {shape.ShapeType} not supported")


class FlatMap:
    """Create a Flat Map of a face.

from importlib import reload
from freecad.Curves import map_on_face

reload(map_on_face)
fm = map_on_face.FlatMap(f1)
sh = fm.compute()
Part.show(sh)

    """

    def __init__(self, face):
        self.Source = face

    def compute(self, scaleX=1.0, scaleY=1.0):
        u0, u1, v0, v1 = self.Source.ParameterRange
        quad = Quad(self.Source.ParameterRange)
        quad.extend(1.0)
        mapper = ShapeMapper(quad.Face, self.Source)
        flat_face = mapper.map_shape(self.Source, True)
        if (scaleX == 1.0) and (scaleY == 1.0):
            return flat_face
        mat = FreeCAD.Matrix()
        mat.scale(scaleX, scaleY, 1.0)
        scaled = flat_face.transformGeometry(mat)
        return scaled


class FlattenFace:
    """Flatten a face.
    """

    def __init__(self, face):
        self.Source = face




class MapOnFace:
    """Map a shape on a target face
    """

    def __init__(self, source, boundary=None):
        self.SourceShape = source.copy()
        self.Boundary = None
        if hasattr(boundary, "copy"):
            self.Boundary = boundary.copy()
        self.SourcePlane = self.get_source_plane()
        self.transform_source()

    def get_source_plane(self):
        if self.Boundary is not None:
            plane = self.Boundary.findPlane()
        else:
            plane = self.SourceShape.findPlane()
        if plane is None:
            raise RuntimeError("Unable to find source plane")
        return plane

    def transform_source(self):
        place = FreeCAD.Placement(self.SourcePlane.Position,
                                  self.SourcePlane.Rotation)
        self.SourceShape.transformShape(place.Matrix.inverse(), False, False)
        if self.Boundary is not None:
            self.Boundary.transformShape(place.Matrix.inverse(), False, False)

    def search_bounds(self, shape=None, margins=[0, 0, 0, 0], search_fac=0.1):
        if not len(margins) == 4:
            raise RuntimeError("margins must have 4 values")
        if shape is None:
            bb = self.SourceShape.BoundBox
        else:
            bb = shape.BoundBox
        if bb.ZLength > 1e-5:
            raise RuntimeError("Source shape is not in XY plane.")
        if search_fac <= 0:
            return [bb.XMin - margins[0],
                    bb.XMax + margins[1],
                    bb.YMin - margins[2],
                    bb.YMax + margins[3]]
        margin_x = search_fac * bb.XLength
        margin_y = search_fac * bb.YLength
        p1 = FreeCAD.Vector(bb.XMin - margin_x, bb.YMin - margin_y, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMin - margin_x, bb.YMax + margin_y, bb.ZMin)
        p3 = FreeCAD.Vector(bb.XMax + margin_x, bb.YMin - margin_y, bb.ZMin)
        p4 = FreeCAD.Vector(bb.XMax + margin_x, bb.YMax + margin_y, bb.ZMin)
        edge = Part.makeLine(p1, p2)
        u0 = self.SourceShape.distToShape(edge)[1][0][0].x - margins[0]
        edge = Part.makeLine(p3, p4)
        u1 = self.SourceShape.distToShape(edge)[1][0][0].x + margins[1]
        edge = Part.makeLine(p1, p3)
        v0 = self.SourceShape.distToShape(edge)[1][0][0].y - margins[2]
        edge = Part.makeLine(p2, p4)
        v1 = self.SourceShape.distToShape(edge)[1][0][0].y + margins[3]
        return u0, u1, v0, v1

    def build_quad(self, face, margins=[0, 0, 0, 0]):
        ssbb = self.search_bounds(self.SourceShape, margins)
        if self.Boundary is None:
            self.quad = Quad(ssbb)
            self.quad.Bounds = face.ParameterRange
        else:
            bobb = self.search_bounds(self.Boundary)
            self.quad = Quad(bobb)
            self.quad.Bounds = face.ParameterRange
            self.quad.extend(ssbb)

    def get_pcurve(self, edge):
        proj = self.quad.Face.project([edge])
        if len(proj.Edges) == 0:
            raise RuntimeError("Failed to get pcurve")
        if len(proj.Edges) > 1:
            FreeCAD.Console.PrintWarning("Projection: several pcurves")
        cos = self.quad.curveOnSurface(proj.Edge1)
        if edge.isClosed() and not cos[0].isClosed():
            FreeCAD.Console.PrintWarning("pcurve should be closed")




"""
from importlib import reload
from freecad.Curves import map_on_face
reload(map_on_face)
q = map_on_face.Quad()
q.Limits = [-2, 5, -1, 10]
q.Limits
q.Bounds
q.Bounds = [-1, 2, -3, 4]
q.Bounds
q.extend(-5, 7, -2, 12)
q.Limits
q.Bounds
q.quad.parameter(FreeCAD.Vector(-2, -1, 0))

"""
