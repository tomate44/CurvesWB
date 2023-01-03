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
        place = FreeCAD.Placement(self.SourcePlane.Position, self.SourcePlane.Rotation)
        self.SourceShape.transformShape(place.Matrix.inverse(), False, False)
        if self.Boundary is not None:
            self.Boundary.transformShape(place.Matrix.inverse(), False, False)

    def search_bounds(self, search_margin=0.1):
        if self.Boundary is None:
            bb = self.SourceShape.BoundBox
        else:
            bb = self.Boundary.BoundBox
        if bb.ZLength > 1e-5:
            raise RuntimeError("Source shape is not in XY plane.")
        if search_margin <= 0:
            return bb.XMin, bb.XMax, bb.YMin, bb.YMax
        margin_x = search_margin * bb.XLength
        margin_y = search_margin * bb.YLength
        p1 = FreeCAD.Vector(bb.XMin - margin_x, bb.YMin - margin_y, bb.ZMin)
        p2 = FreeCAD.Vector(bb.XMin - margin_x, bb.YMax + margin_y, bb.ZMin)
        p3 = FreeCAD.Vector(bb.XMax + margin_x, bb.YMin - margin_y, bb.ZMin)
        p4 = FreeCAD.Vector(bb.XMax + margin_x, bb.YMax + margin_y, bb.ZMin)
        edge = Part.makeLine(p1, p2)
        u0 = self.SourceShape.distToShape(edge)[1][0][0].x
        edge = Part.makeLine(p3, p4)
        u1 = self.SourceShape.distToShape(edge)[1][0][0].x
        edge = Part.makeLine(p1, p3)
        v0 = self.SourceShape.distToShape(edge)[1][0][0].y
        edge = Part.makeLine(p2, p4)
        v1 = self.SourceShape.distToShape(edge)[1][0][0].y
        return u0, u1, v0, v1

    def get_bounds(self, margins=None):
        u0, u1, v0, v1 = self.search_bounds()
        if margins is None:
            return u0, u1, v0, v1
        if not len(margins) == 4:
            raise RuntimeError("margins must have 4 values")
        return [u0 - margins[0],
                u1 + margins[1],
                v0 - margins[2],
                v1 + margins[3]]





