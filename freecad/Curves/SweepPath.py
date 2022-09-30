import FreeCAD
from FreeCAD.Base import Vector
import Part


class SweepPath:
    def __init__(self, path):
        if hasattr(path, "value"):
            self.path = path.toShape()
        elif hasattr(path, "valueAt"):
            self.path = path
        else:
            raise (TypeError, "Path must be a curve or an edge")


class RotationSweepPath(SweepPath):
    def __init__(self, path, center):
        super(RotationSweepPath, self).__init__(path)
        if isinstance(center, Vector):
            self.center = center
        elif isinstance(center, Part.Vertex):
            self.center = center.Point

    def trsfMatrixAt(self, par):
        poc = self.path.valueAt(par)
        v1 = poc - self.center
        der = self.path.derivative1At(par)
        nor = v1.cross(der)
        m = FreeCAD.Matrix()
        m.A11 = v1.x
        m.A12 = der.x
        m.A13 = nor.x
        m.A21 = v1.y
        m.A22 = der.y
        m.A23 = nor.y
        m.A31 = v1.z
        m.A32 = der.z
        m.A33 = nor.z
        print(m.analyze())
        return m

    def localProfile(self, prof, par=None, offset=None):
        if par is None:
            dist, pts, info = prof.distToShape(self.path)
            par = self.path.parameter(pts[0][1])
        if offset is None:
            offset = par
        m = self.trsfMatrixAt(par)
        im = m.inverse()
        locprof = prof.copy()
        for i in range(locprof.NbPoles):
            pole = locprof.getPole(i + 1)
            np = im.multVec(pole)
            np.y += offset
            locprof.setPole(i + 1, np)
        return locprof

    def transformProfiles(self, profiles):
        locprofs = []
        for i, p in enumerate(profiles):
            locprofs.append(self.localProfile(p, None, i))
        return locprofs

    def localLoft(self, profiles):
        locprofs = self.transformProfiles(profiles)
        bs = Part.BSplineSurface()
        bs.buildFromNSections(locprofs)
        return bs


