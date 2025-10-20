# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Curve re-parametrize"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """reparametrize a curve to match another one"""

#import sys
#if sys.version_info.major >= 3:
    #from importlib import reload

import FreeCAD
import Part

from freecad.Curves import nurbs_tools
from freecad.Curves import _utils
from freecad.Curves.BSplineAlgorithms import BSplineAlgorithms




def get_ascending(mylist):
    newlist = []
    old1, old2 = mylist[0]
    for i in range(len(mylist)-1):
        p1, p2 = mylist[i+1]
        if (p1 > old1) and (p2 > old2):
            newlist.append([old1,old2])
        old1 = p1
        old2 = p2
    return newlist

def normalized_bspline(e1, reverse=False):
    bs = None
    if isinstance(e1, Part.Wire):
        bs = e1.approximate(1e-15,1e-7,25,999)
    elif isinstance(e1, Part.Edge):
        bs = e1.Curve.toBSpline(e1.FirstParameter, e1.LastParameter)
    elif isinstance(e1, Part.BSplineCurve):
        bs = e1.copy()
    else:
        _utils.error("{} not supported".format(type(e1)))
    if reverse:
        bs.reverse()
    knots = nurbs_tools.KnotVector(bs)
    bs.setKnots(knots.normalize())
    return bs

def get_ortho_params(e1,e2,n):
    params = list()
    for i in range(n):
        fp, lp = e1.ParameterRange
        p = fp + (lp-fp) * float(i)/(n-1)
        v = e1.valueAt(p)
        d, pts, info = Part.Vertex(v).distToShape(e2)
        if not len(pts) == 1:
            print("found {} points for param {}".format(len(pts), p))
        elif info[0][5]:
            params.append([p,e2.Curve.parameter(pts[0][1])])
    return params

def get_chord_normal_params (e1,e2,n):
    params = list()
    fp, lp = e1.ParameterRange
    chord = Part.makeLine(e1.valueAt(fp), e1.valueAt(lp))
    pts = chord.discretize(n)
    plane = Part.Plane(pts[0],chord.tangentAt(chord.FirstParameter))
    for pt in pts:
        plane.Position = pt
        p1 = e1.Curve.intersect(plane)
        p2 = e2.Curve.intersect(plane)
        print("{} - {}".format(p1,p2))
        try:
            params.append([e1.Curve.parameter(FreeCAD.Vector(p1[0][0].X, p1[0][0].Y, p1[0][0].Z)),
                           e2.Curve.parameter(FreeCAD.Vector(p2[0][0].X, p2[0][0].Y, p2[0][0].Z))])
            print("{}".format(params[-1]))
        except:
            _utils.warn("chord_normal compute error")
    return params

def stretch_params(par, edge, start=0.3, end=0.3):
    #_utils.info(len(par))
    npar = par[:]
    nb_start = int(len(par)*start)
    nb_end = int(len(par)*end)
    if nb_start > 1:
        for i in range(nb_start):
            fac = 1.0 - float(i) / (nb_start-1)
            npar[i] += (edge.FirstParameter - par[0]) * fac
    else:
        npar[0] = edge.FirstParameter
    if nb_end > 1:
        for i in range(nb_end):
            fac = 1.0 - float(i) / (nb_end-1)
            npar[-1-i] += (edge.LastParameter - par[-1]) * fac
    else:
        npar[-1] = edge.LastParameter
    return npar

def deviation_filter(params, tolerance=1e-2):
    """Filter by parametric deviation"""
    new = []
    for i in range(len(params)):
        if abs(params[i][0]-params[i][1]) > tolerance:
            new.append(params[i])
        #else:
            #print("discarding parameter {}/{}".format(i,len(params)))
    return new

def show_lines(e1, e2, params, title=""):
    lines = list()
    for q1,q2 in params:
        lines.append(Part.makeLine(e1.valueAt(q1), e2.valueAt(q2)))
    com = Part.Compound(lines)
    Part.show(com, title)

def get_max_cp(curve, nb_interp):
    max_cp_u = curve.NbPoles
    # we want to use at least 10 and max 80 control points to be able to reparametrize the geometry properly
    mincp = 10
    maxcp = 80
    # since we interpolate the intersections, we cannot use fewer control points than curves
    # We need to add two since we want c2 continuity, which adds two equations
    min_u = max(nb_interp + 2, mincp)
    max_u = max(min_u, maxcp);
    # Clamp(val, min, max) : return std::max(min, std::min(val, max));
    max_cp_u = max(min_u, min(max_cp_u + 10, max_u))
    return max_cp_u

def reparametrize(ie1, ie2, num=20, smooth_start=0.2, smooth_end=0.2, method=3):
    """reparametrize(ie1, ie2, num=20, smooth_start=0.2, smooth_end=0.2, method=0)
    Reparametrize Edge ie2 according to Edge ie1.
    - num is the number of samples
    - smooth_start and smooth_end [0., 0.5] is how much the stretching of the end parameters
    is stretched into the middle of the curve.
    - method option :
    1 - Edge 1 projected on Edge 2
    2 - Edge 2 projected on Edge 1
    3 - Best of methods 1 and 2 by number of results
    4 - Normal plane of chord line
    """
    c1 = normalized_bspline(ie1, False)
    c2 = normalized_bspline(ie2, not _utils.same_direction(ie1, ie2, 10))
    e1 = c1.toShape()
    e2 = c2.toShape()

    if method == 1:
        params = get_ortho_params(e1, e2, num)
        sorted_params = get_ascending(params)
    elif method == 2:
        params = [[p[1],p[0]] for p in get_ortho_params(e2, e1, num)]
        sorted_params = get_ascending(params)
    elif method == 3:
        pa1 = get_ortho_params(e1, e2, num)
        so_pa1 = get_ascending(pa1)
        pa2 = [[p[1],p[0]] for p in get_ortho_params(e2, e1, num)]
        so_pa2 = get_ascending(pa2)
        if len(so_pa2) > len(so_pa1):
            params = pa2
            sorted_params = so_pa2
        else:
            params = pa1
            sorted_params = so_pa1
    else: #elif method == 4:
        params = get_chord_normal_params(e1,e2,num)
        sorted_params = get_ascending(params)
    p1 = [s[0] for s in sorted_params]
    p2 = [s[1] for s in sorted_params]
    gp = [1.0*i/(len(p1)-1) for i in range(len(p1))]

    #show_lines(e1, e2, sorted_params, title="first_pass")

    np1 = stretch_params(p1, e1, start=smooth_start, end=smooth_end)
    np2 = stretch_params(p2, e2, start=smooth_start, end=smooth_end)
    sorted_params = list(zip(np1,np2))
    sorted_params = deviation_filter(sorted_params, 1e-3)

    #show_lines(e1, e2, sorted_params, title="second_pass")

    bsa = BSplineAlgorithms()
    par_tolerance = 1e-15

    nc1 = bsa.reparametrizeBSplineContinuouslyApprox(c1, np1, gp, get_max_cp(c1, num))
    nc2 = bsa.reparametrizeBSplineContinuouslyApprox(c2, np2, gp, get_max_cp(c2, num))
    return nc1, nc2



def main():
    s = FreeCADGui.Selection.getSelectionEx()
    edges = []
    for so in s:
        for su in so.SubObjects:
            #subshapes(su)
            if isinstance(su, Part.Edge):
                edges.append(su)
        if not so.HasSubObjects:
            edges.append(so.Object.Shape.Wires[0])

    nc1, nc2 = reparametrize(edges[0], edges[1], 40)
    com2 = Part.Compound([nc1.toShape(), nc2.toShape()])
    Part.show(com2)

if __name__ == "__main__":
    main()
