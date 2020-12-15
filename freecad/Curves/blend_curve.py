# -*- coding: utf-8 -*-

__title__ = ""
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """"""

from time import time

import FreeCAD
import FreeCADGui
import Part

CAN_MINIMIZE = True

try:
    from scipy.optimize import minimize
except ImportError:
    CAN_MINIMIZE = False

vec3 = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d


class BlendCurve:
    def __init__(self, constraints=[]):
        self.constraints = constraints
        self.scales = [1.0] * len(constraints)
        self.curve = Part.BezierCurve()
        self.nb_samples = 32

    @staticmethod
    def can_minimize():
        try:
            from scipy.optimize import minimize
            return True
        except ImportError:
            return False

    @classmethod
    def from_edge_constraints(cls, cons_list):
        """Create the blend curve from a list of edge constraints
        Each edge constraint is a tuple : (edge, parameter, continuity)"""
        constraints = []
        for tup in cons_list:
            constraints.append([tup[0].Curve.getDN(tup[1], i) for i in range(0, tup[2] + 1)])
        return cls(constraints)

    def perform(self):
        """Scale the constraints, and interpolate them"""
        cons = self.scale_constraints()
        self.curve.interpolate(cons)
        return  # self.solver.solve(self.matrix, cons[0], cons[1])

    def add_constraint(self, edge, param, n):
        """add a constraint for edge, at param, with continuity Gn"""
        res = [edge.Curve.getDN(param, i) for i in range(0, n + 1)]
        self.constraints.append(res)
        self.scales.append(1.0)

    def scale_constraint(self, constraint, scale):
        res = []
        for i in range(len(constraint)):
            res.append(constraint[i] * pow(scale, i))
        return res

    def scale_constraints(self):
        scaled_constraints = []
        for i, veclist in enumerate(self.constraints):
            scaled_constraints.append(self.scale_constraint(veclist, self.scales[i]))
        return scaled_constraints

    def normalize_constraints(self):
        """Compute scales so that the tangent of constraints is 1.0"""
        scales = []
        for cons in self.constraints:
            if len(cons) > 1:
                tan = cons[1].Length
                if tan > 1e-5:
                    scales. append(1.0 / tan)
                    print("Scaled to : {}".format(1.0 / tan))
                else:
                    scales. append(1.0)
                    print("tangent too small. Ignoring")
            else:
                scales.append(1.0)
        self.scales = scales

    def auto_orient(self):
        """Compute scales so that the tangent of each constraint points toward the following one"""
        if len(self.constraints) < 2:
            return
        cons = self.constraints + [self.constraints[-2]]
        for i in range(len(cons) - 1):
            if len(cons[i]) > 1:
                direction = cons[i + 1][0] - cons[i][0]
                dot = direction.dot(cons[i][1])
                if dot < 0:
                    self.scales[i] *= -1.0
        self.scales[-1] *= -1.0

    # Curve evaluation methods
    def curvature_regularity_score(self, scales):
        self.scales = scales
        self.perform()
        curva_list = [self.curve.curvature(p / self.nb_samples) for p in range(self.nb_samples + 1)]
        return max(curva_list) - min(curva_list)

    def cp_regularity_score(self, scales):
        self.scales = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        lenghts = [e.Length for e in poly.Edges]
        return max(lenghts) - min(lenghts)

    def total_cp_angular(self, scales):
        self.scales = scales
        self.perform()
        poly = Part.makePolygon(self.curve.getPoles())
        # min_angle = poly.Edges[0].Curve.Direction.getAngle(poly.Edges[-1].Curve.Direction)
        angles = []
        for i in range(1, len(poly.Edges)):
            angles.append(poly.Edges[i - 1].Curve.Direction.getAngle(poly.Edges[i].Curve.Direction))
        return max(angles) - min(angles)

    def set_regular_poles(self):
        res = minimize(self.cp_regularity_score, self.scales, method='Nelder-Mead', options={"maxiter":2000, "disp":True})

    def minimize_curvature(self):
        res = minimize(self.curvature_regularity_score, self.scales, method='Nelder-Mead', options={"maxiter":2000, "disp":True})

    def minimize_angular_variation(self):
        res = minimize(self.total_cp_angular, self.scales, method='Nelder-Mead', options={"maxiter":2000, "disp":True})


def main():

    # selection
    edges = []
    vertexes = []
    s = FreeCADGui.Selection.getSelectionEx()
    for so in s:
        for su in so.SubObjects:
            if isinstance(su, Part.Edge):
                edges.append(su)
            elif isinstance(su, Part.Vertex):
                vertexes.append(su)

    start = time()
    blend_curve = BlendCurve.from_edge_constraints([(edges[0], 0.0, 3),(edges[1], 0.0, 3)])
    blend_curve.nb_samples = 200
    blend_curve.normalize_constraints()
    blend_curve.auto_orient()
    blend_curve.minimize_curvature()  # minimize_curvature()
    print("Minimize time = {}s".format(time()-start))
    print("Final scales = {} - {}".format(*blend_curve.scales))
    Part.show(blend_curve.curve.toShape())

if __name__ == '__main__':
    main()
