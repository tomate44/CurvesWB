import FreeCAD
import FreeCADGui
import Part

"""
from freecad.Curves import PointInterpolation
pi = PointInterpolation.PointInterpolation(vl)
pi.Periodic = True
pi.set_parameters("ChordLength")
c = pi.interpolate()
Part.show(c.toShape())

"""


class PointInterpolation:
    """Interpolate a list of points with a BSpline curve"""
    def __init__(self, points):
        if isinstance(points[0], Part.Vertex):
            pts = [v.Point for v in points]
        else:
            pts = points
        self.Tolerance = FreeCAD.Base.Precision.confusion()
        self.Closed = False
        self.Periodic = False
        self.Degenerated = False
        if self.are_degenerated(pts):
            self.Points = pts
            self.Degenerated = True
        elif pts[0].distanceToPoint(pts[-1]) < self.Tolerance:
            FreeCAD.Console.PrintError("Closed point list\n")
            self.Closed = True
            self.Point = pts[:-1]
        else:
            self.Points = pts
        self.set_parameters()

    def are_degenerated(self, pts):
        "Return True if ALL points are at the same location"
        for i in range(1, len(pts)):
            if pts[i].distanceToPoint(pts[i - 1]) > self.Tolerance:
                return False
        FreeCAD.Console.PrintMessage("Degenerated point list\n")
        return True

    def get_parameters(self, arg="ChordLength"):
        self.Parametrization = arg
        if arg == "ChordLength":
            return self.get_parameters(1.0)
        elif arg == "Centripetal":
            return self.get_parameters(0.5)
        elif arg == "Uniform":
            return self.get_parameters(0.0)
        elif arg == "MainChord":
            line = Part.Line(self.Points[0], self.Points[0] + self.Points[-1])
            return self.get_parameters(line)
        elif hasattr(arg, "parameter"):
            params = [arg.parameter(self.Points[0])]
            for i in range(1, len(self.Points)):
                par = arg.parameter(self.Points[i])
                if par > params[-1]:
                    params.append(par)
                else:
                    FreeCAD.Console.PrintError("Parameters are not increasing\n")
                    FreeCAD.Console.PrintError("Falling back to ChordLength\n")
                    return self.get_parameters("ChordLength")
                    break
            return params
        elif (arg >= 0.0) and (arg <= 1.0):
            params = [0.0]
            pts = self.Points[:]
            if self.Closed or self.Periodic:
                pts.append(pts[0])
            for i in range(1, len(pts)):
                p = pts[i] - pts[i - 1]
                le = p.Length
                pl = pow(le, arg)
                params.append(params[-1] + pl)
            return params

    def set_parameters(self, arg="ChordLength"):
        if isinstance(arg, (list, tuple)):
            self.Parameters = arg
        else:
            self.Parameters = self.get_parameters(arg)
        # else:
        #     FreeCAD.Console.PrintError("Bad number of Parameters\n")
        #     FreeCAD.Console.PrintError("Falling back to ChordLength\n")
        #     self.Parameters = self.get_parameters("ChordLength")

    def interpolate_periodic(self):
        pts = self.Points[:]
        nbp = len(pts)
        n = 1
        if nbp <= 4:
            n = 2

        npts = pts
        npts.extend(pts * (2 * n))
        # nbnp = len(npts)
        # interpolate the extended list of points
        pi = self.__class__(npts)
        pi.Periodic = True
        pi.set_parameters(self.Parametrization)
        bs = Part.BSplineCurve()
        print(len(npts), len(pi.Parameters), pi.Parameters)
        bs.interpolate(Points=npts, Parameters=pi.Parameters, PeriodicFlag=True)
        # extract a one turn BSpline curve in the middle
        offset = n * nbp
        npoles = bs.getPoles()[offset:-offset - 1]
        nmults = bs.getMultiplicities()[offset:-offset]
        nknots = bs.getKnots()[offset:-offset]
        nbs = Part.BSplineCurve()
        print(len(npoles), nmults, nknots, True, 3)
        nbs.buildFromPolesMultsKnots(npoles, nmults, nknots, True, 3)
        return nbs

    def interpolate(self):
        if self.Periodic:
            return self.interpolate_periodic()
        npts = self.Points[:]
        if self.Closed:
            npts.append(npts[0])
        bs = Part.BSplineCurve()
        bs.interpolate(Points=npts, Parameters=self.Parameters)
        return bs


