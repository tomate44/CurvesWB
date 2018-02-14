import math
import FreeCAD
import Part

def error(s):
    FreeCAD.Console.PrintError(s)

def getTrimmedCurve(e):
    c = e.Curve.copy().toBSpline()
    if (not e.FirstParameter == c.FirstParameter) or (not e.LastParameter == c.LastParameter):
        c.segment(e.FirstParameter, e.LastParameter)
        return(c)
    return(c)

def trim(curve,min,max,length,tol):
    c = curve.copy()
    mid = (max + min) * 0.5
    c.segment(c.FirstParameter,mid)
    #print(mid)
    r = None
    if abs(c.length() - length) < tol:
        #print("Found at %f"%mid)
        return(c)
    elif c.length() < length:
        r = trim(curve,mid,max,length,tol)
    elif c.length() > length:
        r = trim(curve,min,mid,length,tol)
    return(r)
    

def trimToLength(ed, l, tol = 1e-5):
    if l > ed.Length:
        return(False)
    r = trim(ed.Curve,ed.Curve.FirstParameter,ed.Curve.LastParameter,l,tol)
    return(r.toShape())



def extendCurve( curve, end = 1, scale = 1, degree = 1):
    if scale <= 0:
        return(curve)
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
        bez.setPoles([val,val.add(tan)])
        return(bez)

    # Degree 2 extension (G2)

    try:
        nor = curve.normal(p)
        cur = curve.curvature(p)
    except Part.OCCError:
        # the curve is probably straight
        bez.setPoles([val,val.add(tan/2),val.add(tan)])
        return(bez)
    radius = cur * pow(tan.Length,2) * degree / (degree - 1)
    # radius = 2 * cur * pow( tan.Length, 2)
    opp = math.sqrt(abs(pow(scale,2)-pow(radius,2)))
    c = Part.Circle()
    c.Axis = tan
    v = FreeCAD.Vector(tan)
    v.normalize().multiply(tan.Length+opp)
    c.Center = val.add(v)
    c.Radius = radius
    plane = Part.Plane(val,c.Center,val.add(nor))
    pt = plane.intersect(c)[0][1] # 2 solutions
    p2 = FreeCAD.Vector(pt.X,pt.Y,pt.Z)
    bez.setPoles([val,val.add(tan),p2])
    # cut to the right length
    nc = trim(bez, bez.FirstParameter, bez.LastParameter, scale, 1e-5)
    return(nc)

def extendToPoint( curve, pt, end = 1, degree = 1):
    ''' bezierCurveExtension = curveExtend.extendToPoint( curve, point, end=[0|1], degree=[1|2]) '''
    if end == 0:
        val = curve.value(curve.FirstParameter)
    else:
        val = curve.value(curve.LastParameter)
    dist = val.distanceToPoint(pt)
    ratio = 1.0 * degree / (degree + 1)
    
    bez = extendCurve( curve, end, dist * ratio, degree)
    nbez = Part.BezierCurve()
    nbez.setPoles(bez.getPoles()+[pt])
    return(nbez)

