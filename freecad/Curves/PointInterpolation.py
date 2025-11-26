# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
from . import TOL3D

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
    def __init__(self, points, periodic=False):
        if isinstance(points[0], Part.Vertex):
            self.Points = [v.Point for v in points]
        else:
            self.Points = points
        self.Tolerance = TOL3D
        self.Periodic = periodic
        self.check_duplicates()
        if self.Periodic and (not self.Duplicates) and self.are_closed():
            FreeCAD.Console.PrintMessage("Periodic interpolation\n")
            FreeCAD.Console.PrintMessage("Ignoring duplicate last point\n")
            self.Points = points[:-1]

    def are_closed(self):
        if self.Points[0].distanceToPoint(self.Points[-1]) < self.Tolerance:
            return True
        return False

    def check_duplicates(self):
        "Return True if ALL points are at the same location"
        self.Duplicates = True
        for i in range(1, len(self.Points)):
            if self.Points[i].distanceToPoint(self.Points[i - 1]) > self.Tolerance:
                self.Duplicates = False
                break
        FreeCAD.Console.PrintMessage("Duplicates point list\n")
        return self.Duplicates

    def parameters_along_curve(self, curve):
        pts = self.Points[:]
        if self.Periodic:
            pts.append(pts[0])
        params = [curve.parameter(self.Points[0])]
        for i in range(1, len(self.Points)):
            par = curve.parameter(self.Points[i])
            if par > params[-1]:
                params.append(par)
            else:
                FreeCAD.Console.PrintError("Parameters are not increasing\n")
                FreeCAD.Console.PrintError("Falling back to ChordLength\n")
                params = self.get_parameters("ChordLength")
                break
        return params

    def parameters_from_factor(self, factor):
        params = [0.0]
        pts = self.Points[:]
        if self.Periodic:
            pts.append(pts[0])
        for i in range(1, len(pts)):
            p = pts[i] - pts[i - 1]
            le = p.Length
            pl = pow(le, factor)
            params.append(params[-1] + pl)
        return params

    def get_parameters(self, arg="ChordLength"):
        self.Parametrization = arg
        if self.Duplicates:
            self.Parametrization = "Uniform"
            return list(range(len(self.Points)))
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
            return self.parameters_along_curve(arg)
        elif (arg >= 0.0) and (arg <= 1.0):
            return self.parameters_from_factor(arg)

    def set_parameters(self, arg="ChordLength"):
        if isinstance(arg, (list, tuple)):
            extra = 0
            if self.Periodic:
                extra = 1
            if len(arg) == (len(self.Points) + extra):
                self.Parameters = arg
            else:
                raise (ValueError, "Number of points and parameters mismatch")
        else:
            self.Parameters = self.get_parameters(arg)

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

    def interpolate(self, pts=self.Points):
        if self.Duplicates:
            tmp = [FreeCAD.Vector(i, 0, 0) for i in range(len(self.Points))]
            c = self.interpolate(tmp)
            c.setPoles([self.Points[0]] * c.NbPoles)
            
        if self.Periodic:
            return self.interpolate_periodic()
        npts = self.Points[:]
        bs = Part.BSplineCurve()
        bs.interpolate(Points=npts, Parameters=self.Parameters)
        return bs


def test():
    pts = [FreeCAD.Vector(0, 0, 0),
           FreeCAD.Vector(5, 0, 0),
           FreeCAD.Vector(6, 1, 0),
           FreeCAD.Vector(0, 2, 0)]
    pi = PointInterpolation(pts)
    for arg in ["ChordLength", "Centripetal", "Uniform", 0.2, 0.9]:
        pi.set_parameters(arg)
        c = pi.interpolate()
        Part.show(c.toShape(), str(arg))
    pi.Periodic = True
    for arg in ["ChordLength", "Centripetal", "Uniform", 0.2, 0.9]:
        pi.set_parameters(arg)
        c = pi.interpolate()
        Part.show(c.toShape(), str(arg) + "_periodic")

    pts2 = [FreeCAD.Vector(0, 0, 0)] * 5
    pi = PointInterpolation(pts2)
    for arg in ["ChordLength", "Centripetal", "Uniform", 0.2, 0.9]:
        pi.set_parameters(arg)
        c = pi.interpolate()
        Part.show(c.toShape(), str(arg))
    pi.Periodic = True
    for arg in ["ChordLength", "Centripetal", "Uniform", 0.2, 0.9]:
        pi.set_parameters(arg)
        c = pi.interpolate()
        Part.show(c.toShape(), str(arg) + "_periodic")
