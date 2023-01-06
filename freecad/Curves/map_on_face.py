import FreeCAD
import FreeCADGui
import Part


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
            self.setPoles(*bounds)

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
        if not (len(bounds) == 4):
            raise RuntimeError("Quad need 4 bounds")
        u0, u1, v0, v1 = self.Limits
        s0, s1, t0, t1 = bounds
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
        self.Limits = bounds
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


class MapOnFace:
    """Map a shape on a target face
    """

    def __init__(self, source, boundary=None):
        self.SourceShape = source.copy()
        self.Boundary = None
        if hasattr(boundary, "copy"):
            self.Boundary = boundary.copy()
        self.SourcePlane = self.get_source_plane()

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

    def search_bounds(self, shape=None, search_fac=0.1, margins=[0, 0, 0, 0]):
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


"""
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
