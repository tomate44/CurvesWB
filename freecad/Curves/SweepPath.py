import FreeCAD
import FreeCADGui
from FreeCAD import Vector
import Part


class SweepProfile:
    def __init__(self, prof, par=None):
        self.param = par
        if hasattr(prof, "value"):
            self.curve = prof.toBSpline()
        elif hasattr(prof, "Curve"):
            self.curve = prof.Curve.toBSpline()
        elif isinstance(prof, Part.Wire):
            self.curve = prof.approximate(1e-10, 1e-7, 10000, 3)

    @property
    def Curve(self):
        return self.curve

    @property
    def Shape(self):
        return self.curve.toShape()

    @property
    def Parameter(self):
        return self.param

    @Parameter.setter
    def Parameter(self, p):
        self.param = p


class SweepPath:
    def __init__(self, path):
        self.profiles = []
        if hasattr(path, "value"):
            self.path = path.toShape()
        elif hasattr(path, "valueAt"):
            self.path = path
        else:
            raise (TypeError, "Path must be a curve or an edge")

    def add_profile(self, prof):
        dist, pts, info = self.path.distToShape(prof)
        par = self.path.Curve.parameter(pts[0][0])
        self.profiles.append(SweepProfile(prof, par))

    def sort_profiles(self):
        self.profiles.sort(key=lambda x: x.Parameter)


class RotationSweepPath(SweepPath):
    def __init__(self, path, center):
        super(RotationSweepPath, self).__init__(path)
        if isinstance(center, Vector):
            self.center = center
        elif isinstance(center, Part.Vertex):
            self.center = center.Point

    def transitionMatrixAt(self, par):
        poc = self.path.valueAt(par)
        cho = self.center - poc
        der = self.path.tangentAt(par)  # derivative1At(par)
        nor = cho.cross(der)
        m = FreeCAD.Matrix(cho.x, der.x, nor.x, poc.x,
                           cho.y, der.y, nor.y, poc.y,
                           cho.z, der.z, nor.z, poc.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        return m

    def computeLocalProfile(self, prof):
        m = self.transitionMatrixAt(prof.Parameter)
        m = m.inverse()
        locprof = prof.Curve.copy()
        for i in range(locprof.NbPoles):
            pole = locprof.getPole(i + 1)
            np = m.multVec(pole)
            # np.y += prof.Parameter
            locprof.setPole(i + 1, np)
        # print(locprof.getPole(1))
        # print(locprof.getPole(locprof.NbPoles))
        prof.locCurve = locprof
        return locprof

    def add_profile(self, prof):
        if isinstance(prof, (list, tuple)):
            for p in prof:
                self.add_profile(p)
            return
        sp = SweepProfile(prof)
        dist, pts, info = self.path.distToShape(sp.Shape)
        sp.Parameter = self.path.Curve.parameter(pts[0][0])
        self.computeLocalProfile(sp)
        self.profiles.append(sp)
        print(f"Profile added at {sp.Parameter}")

    def interpolate_profiles(self):
        self.sort_profiles()
        locprofs = [p.locCurve for p in self.profiles]
        bs = Part.BSplineSurface()
        bs.buildFromNSections(locprofs)
        fp, lp = self.profiles[0].Parameter, self.profiles[-1].Parameter
        bs.scaleKnotsToBounds(0.0, 1.0, fp, lp)
        self.localLoft = bs
        return bs

    def get_profile(self, par):
        locprof = self.localLoft.vIso(par)
        m = self.transitionMatrixAt(par)
        for i in range(locprof.NbPoles):
            pole = locprof.getPole(i + 1)
            # pole.y -= par
            np = m.multVec(pole)
            locprof.setPole(i + 1, np)
        # print(locprof.getPole(1))
        # print(locprof.getPole(locprof.NbPoles))
        return locprof


sel = FreeCADGui.Selection.getSelectionEx()
el = []
for so in sel:
    el.extend(so.SubObjects)

center = el[1].valueAt(el[1].FirstParameter)
rsp = RotationSweepPath(el[0], center)
rsp.add_profile(el[1:])
rsp.interpolate_profiles()

Part.show(rsp.localLoft.toShape())

for i, p in enumerate(rsp.profiles[1:-1]):
    # Part.show(p.Shape)
    Part.show(rsp.get_profile(p.Parameter).toShape())

for pt in rsp.path.discretize(10):
    p = rsp.path.Curve.parameter(pt)
    iso = rsp.get_profile(p)
    Part.show(iso.toShape(), f"Profile@{p}")



