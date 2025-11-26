# SPDX-License-Identifier: LGPL-2.1-or-later

import math
import FreeCAD
import Part


def error(s):
    FreeCAD.Console.PrintError(s)


def getTrimmedCurve(e):
    """Get a trimmed BSpline curve from an edge."""
    try:
        c = e.toNurbs().Edge1.Curve
    except Exception as exc:
        error(f"CurveExtend : Nurbs conversion error\n{exc}\n")
        c = e.Curve.toBSpline()
    if (not e.FirstParameter == c.FirstParameter) or (not e.LastParameter == c.LastParameter):
        FreeCAD.Console.PrintWarning("Segmenting input curve\n")
        c.segment(e.FirstParameter, e.LastParameter)
    return c


def trim(curve, min_, max_, length, tol):
    """recursive function to trim a geometry curve to a given length.
    Should not be useful anymore."""
    c = curve.copy()
    mid = (max_ + min_) * 0.5
    c.segment(c.FirstParameter, mid)
    # print(mid)
    r = None
    if abs(c.length() - length) < tol:
        # print("Found at %f"%mid)
        return c
    elif c.length() < length:
        r = trim(curve, mid, max_, length, tol)
    elif c.length() > length:
        r = trim(curve, min_, mid, length, tol)
    return r


def trimToLength(ed, le, tol=1e-5):
    """Trim an edge to a given length."""
    if le > ed.Length:
        return False
    r = trim(ed.Curve, ed.Curve.FirstParameter, ed.Curve.LastParameter, le, tol)
    return r.toShape()


def extendCurve(curve, end=1, scale=1, degree=1):
    if scale <= 0:
        return curve
    if end == 0:
        p = curve.FirstParameter
        sc = -scale
    else:
        p = curve.LastParameter
        sc = scale

    val = curve.value(p)
    tan = curve.tangent(p)[0]
    tan.normalize()
    tan.multiply(sc)

    bez = Part.BezierCurve()

    if degree == 1:
        bez.setPoles([val, val.add(tan)])
        return(bez)

    # Degree 2 extension (G2)

    try:
        nor = curve.normal(p)
        cur = curve.curvature(p)
    except Part.OCCError:
        # the curve is probably straight
        bez.setPoles([val, val.add(tan / 2), val.add(tan)])
        return bez
    radius = cur * pow(tan.Length, 2) * degree / (degree - 1)
    # radius = 2 * cur * pow( tan.Length, 2)
    opp = math.sqrt(abs(pow(scale, 2) - pow(radius, 2)))
    c = Part.Circle()
    c.Axis = tan
    v = FreeCAD.Vector(tan)
    v.normalize().multiply(tan.Length + opp)
    c.Center = val.add(v)
    c.Radius = radius
    plane = Part.Plane(val, c.Center, val.add(nor))
    pt = plane.intersect(c)[0][1]  # 2 solutions
    p2 = FreeCAD.Vector(pt.X, pt.Y, pt.Z)
    bez.setPoles([val, val.add(tan), p2])
    # cut to the right length
    # nc = trim(bez, bez.FirstParameter, bez.LastParameter, scale, 1e-5)
    nc = bez.copy()
    e = bez.toShape()
    p = e.getParameterByLength(scale)
    nc.segment(c.FirstParameter, p)
    return nc


def extendToPoint(curve, pt, end=1, degree=1):
    ''' bezierCurveExtension = curveExtend.extendToPoint( curve, point, end=[0|1], degree=[1|2]) '''
    if end == 0:
        val = curve.value(curve.FirstParameter)
    else:
        val = curve.value(curve.LastParameter)
    dist = val.distanceToPoint(pt)
    ratio = 1.0 * degree / (degree + 1)

    bez = extendCurve(curve, end, dist * ratio, degree)
    nbez = Part.BezierCurve()
    nbez.setPoles(bez.getPoles() + [pt])
    return nbez
