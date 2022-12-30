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
        self.SourceShape = source
        self.Boundary = boundary
        self.SourcePlane = self.get_source_plane()

    def get_source_plane(self):
        if self.Boundary is not None:
            plane = self.Boundary.findPlane()
        else:
            plane = self.SourceShape.findPlane()
        if plane is None:
            raise("Unable to find source plane")
        return plane

    def transform_source(self, placement=FreeCAD.Placement()):
        self.SourceShape.translate(-self.SourcePlane.Position)
        self.SourceShape.rotate(self.SourcePlane.Rotation.inverted())
        if self.Boundary is not None:
            self.Boundary.translate(-self.SourcePlane.Position)
            self.Boundary.rotate(self.SourcePlane.Rotation.inverted())

    def source_bounds(self):
        bb = self.SourceShape.BoundBox
        edge = Part.makeLine(FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin), FreeCAD.Vector(bb.XMin, bb.YMax, bb.ZMin))
        u0 = self.SourceShape.distToShape(edge)[1][0][0].X
        edge = Part.makeLine(FreeCAD.Vector(bb.XMax, bb.YMin, bb.ZMin), FreeCAD.Vector(bb.XMax, bb.YMax, bb.ZMin))
        u1 = self.SourceShape.distToShape(edge)[1][0][0].X
        edge = Part.makeLine(FreeCAD.Vector(bb.XMin, bb.YMin, bb.ZMin), FreeCAD.Vector(bb.XMax, bb.YMin, bb.ZMin))
        v0 = self.SourceShape.distToShape(edge)[1][0][0].Y
        edge = Part.makeLine(FreeCAD.Vector(bb.XMin, bb.YMax, bb.ZMin), FreeCAD.Vector(bb.XMax, bb.YMax, bb.ZMin))
        v1 = self.SourceShape.distToShape(edge)[1][0][0].Y
        return u0, u1, v0, v1

    def add_margins



