import math
import FreeCAD
import Part

def error(s):
    FreeCAD.Console.PrintError(s)

def getTrimmedCurve(e):
    c = e.Curve.copy()
    if (not e.FirstParameter == c.FirstParameter) or (not e.LastParameter == c.LastParameter):
        c.segment(e.FirstParameter, e.LastParameter)
        return(c)
    return(c)

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

    nor = curve.normal(p)
    cur = curve.curvature(p)
    
    #if cur < 1e-6:
        #bez.setPoles([val,val.add(tan)])
        #return(bez)

    radius = 2 * cur * pow( tan.Length, 2)
    opp = math.sqrt(abs(pow(scale,2)-pow(radius,2)))
    c = Part.Circle()
    c.Axis = tan
    v = FreeCAD.Vector(tan)
    v.normalize().multiply(tan.Length+opp)
    c.Center = val.add(v)
    c.Radius = radius
    plane = Part.Plane(val,c.Center,val.add(nor))
    #print(plane)
    pt = plane.intersect(c)[0][1] # 2 solutions
    #print(pt)
    p2 = FreeCAD.Vector(pt.X,pt.Y,pt.Z)

    bez.setPoles([val,val.add(tan),p2])
    # cut to the right length
    e = bez.toShape()
    parm = e.getParameterByLength(scale)
    bez.segment(bez.FirstParameter,parm)
    return(bez)

