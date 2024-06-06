import FreeCAD
import Part
from freecad.Curves.curveOnSurface import curveOnSurface
from freecad.Curves import nurbs_tools


class blendSurface:
    def __init__(self, ef1, ef2):
        self.ef1 = ef1
        self.ef2 = ef2
        self.Scales = [[1.0, 1.0]]

    def reverse(self):
        ori = self.ef2[0].Orientation
        self.ef2[0].reverse()
            if ori == self.ef2[0].Orientation:
                raise (RuntimeError, "Edge reverse failed")

    def untwist(self):
        pass

    def check_samerange(self):
        return True

    def uniform_parameters(self, n):
        num = max(2, n)
        iso0 = self.ruled_face.Surface.vIso(0.0)
        iso1 = self.ruled_face.Surface.vIso(1.0)
        params = []
        for i in range(num):
            d = i / (num - 1)
            p1 = iso0.parameterAtDistance(d * iso0.length())
            p2 = iso1.parameterAtDistance(d * iso1.length())
            params.append((p1 + p2) / 2)
        return params

    def scaling_curve(self, linear=False):
        scale = self.Scales
        if len(scales) == 1:
            scales *= 2
        params = self.uniform_parameters(len(scales))
        pts = []
        for i in range(len(scales)):
            pts.append(FreeCAD.Vector(scales[i][0], scales[i][1], params[i]))
        bs = Part.BSplineCurve()
        degree = 2
        if linear:
            degree = 1
        bs.approximate(Points=pts, DegMin=degree, DegMax=degree,
                       Parameters=params, Tolerance=1e-7)
        return bs

    def perform(self, reverse=False):
        self.untwist()
        if reverse:
            self.reverse()
        ruled_surf = self.ruled_surface().Surface
        ruled_surf.scaleKnotsToBounds()
        ruled_face = ruled_surf.toShape()
        shell = Part.Shell([self.ef1[1], ruled_face, self.ef2[1]])
        self.ruled_face = shell.Face2
        for e in self.ruled_face.Edges:
            if shell.Face1.curveOnSurface(e):
                self.ef1 = [e, shell.Face1]
            if shell.Face3.curveOnSurface(e):
                self.ef2 = [e, shell.Face3]
        scales = self.scaling_curve()
        dirvec = self.direction_curve()
        sample_params = self.uniform_parameters(self.NbSamples)
        for par in sample_params:
            iso = self.ruled_face.Surface.uIso(par)
            # direction = iso.value(1.0) - iso.value(0.0)
            cos1 = self.ef1[1].curveOnSurface(self.ef1[0])[0]
            curvepar1 = cos1.value(par)
            lcs1 = self.lcs(self.ef1, curvepar1)
            bp1 = BlendPoint()
            cos2 = self.ef2[1].curveOnSurface(self.ef2[0])[0]

