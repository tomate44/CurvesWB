# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Curves workbench utilities"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Curves workbench utilities common to all tools."

import FreeCAD
import Part


def setIconsPath(path):
    global icons_path
    icons_path = path
    return True


def iconsPath():
    global icons_path
    return icons_path


def info(string):
    FreeCAD.Console.PrintMessage("{}\n".format(string))


def warn(string):
    FreeCAD.Console.PrintWarning("{}\n".format(string))


def error(string):
    FreeCAD.Console.PrintError("{}\n".format(string))


def debug(string):
    FreeCAD.Console.PrintMessage("{}\n".format(string))


def doNothing(string):
    return None


def setEditorMode(fp, group, mode):
    """set the editor mode of a group of properties"""
    for prop in group:
        fp.setEditorMode(prop, mode)


def getSubShape(shape, shape_type, n):
    if shape_type == "Vertex" and len(shape.Vertexes) >= n:
        return shape.Vertexes[n - 1]
    elif shape_type == "Edge" and len(shape.Edges) >= n:
        return shape.Edges[n - 1]
    elif shape_type == "Face" and len(shape.Faces) >= n:
        return shape.Faces[n - 1]
    else:
        return None


def getShape(obj, prop, shape_type):
    if hasattr(obj, prop) and obj.getPropertyByName(prop):
        prop_link = obj.getPropertyByName(prop)
        if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSub":
            if shape_type in prop_link[1][0]:
                try:  # FC 0.19+ to make links work without getGlobalPlacement()
                    return prop_link[0].getSubObject(prop_link[1][0])
                except AttributeError:  # FC 0.18 (stable)
                    n = eval(obj.getPropertyByName(prop)[1][0].lstrip(shape_type))
                    osh = obj.getPropertyByName(prop)[0].Shape
                    sh = osh.copy()
                    if sh and (not shape_type == "Vertex") and hasattr(obj.getPropertyByName(prop)[0], "getGlobalPlacement"):
                        pl = obj.getPropertyByName(prop)[0].getGlobalPlacement()
                        sh.Placement = pl
                    return getSubShape(sh, shape_type, n)

        elif obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
            res = []
            for tup in prop_link:
                for ss in tup[1]:
                    if shape_type in ss:
                        try:  # FC 0.19+
                            res.append(tup[0].getSubObject(ss))
                        except AttributeError:  # FC 0.18 (stable)
                            n = eval(ss.lstrip(shape_type))
                            sh = tup[0].Shape.copy()
                            if sh and (not shape_type == "Vertex") and hasattr(tup[0], "getGlobalPlacement"):
                                pl = tup[0].getGlobalPlacement()
                                sh.Placement = pl
                            res.append(getSubShape(sh, shape_type, n))
            return res
        else:
            FreeCAD.Console.PrintError("CurvesWB._utils.getShape: wrong property type.\n")
            return None
    else:
        # FreeCAD.Console.PrintError("CurvesWB._utils.getShape: %r has no property %r\n"%(obj, prop))
        return None


def same_direction(e1, e2, num=10):
    """bool = same_direction(e1, e2, num=10)
    Check if the 2 entities have same direction,
    by comparing them on 'num' samples.
    Entities can be : edges, wires or curves
    """
    v1 = []
    v2 = []
    pts1 = e1.discretize(num)
    pts2 = e2.discretize(num)
    for i in range(num):
        v1.append(pts1[i].distanceToPoint(pts2[i]))
        v2.append(pts1[i].distanceToPoint(pts2[num - 1 - i]))
    if sum(v1) < sum(v2):
        return True
    else:
        return False


def info_subshapes(shape):
    """Print the list of subshapes of a shape in FreeCAD console.
    info_subshapes(my_shape)
    """
    sh = ["Solids",
          "Compounds",
          "CompSolids",
          "Shells",
          "Faces",
          "Wires",
          "Edges",
          "Vertexes"]
    info("-> Content of {}".format(shape.ShapeType))
    for s in sh:
        subs = shape.__getattribute__(s)
        if subs:
            if (len(subs) == 1) and (subs[0].isEqual(shape)):
                pass  # hide self
            else:
                info("{}: {}".format(s, len(subs)))


def ancestors(shape, sub):
    '''list_of_shapes = ancestors(shape, sub)
    Returns the closest ancestors of "sub" in "shape"'''
    def cleanup(shape):
        s = str(shape)
        ss = s.split()[0]
        return ss.split('<')[1]
    shd = (Part.Vertex,
           Part.Edge,
           Part.Wire,
           Part.Face,
           Part.Shell,
           Part.Solid,
           Part.CompSolid,
           Part.Compound)
    for i in range(len(shd) - 1):
        if isinstance(sub, shd[i]):
            for j in range(i + 1, len(shd)):
                manc = shape.ancestorsOfType(sub, shd[j])
                if manc:
                    print("{} belongs to {} {}.".format(cleanup(sub),
                                                        len(manc),
                                                        cleanup(manc[0])))
                    return manc


def rootNode(shape, mode=2, deviation=0.3, angle=0.4):
    buf = shape.writeInventor(mode, deviation, angle)
    from pivy import coin
    inp = coin.SoInput()
    inp.setBuffer(buf)
    node = coin.SoDB.readAll(inp)
    return node


def ruled_surface(e1, e2, normalize=False):
    """creates a ruled surface between 2 edges or wires, with automatic orientation."""
    def wire_and_endpoints(sh):
        pts = sh.discretize(10)
        if isinstance(sh, Part.Edge):
            return Part.Wire([sh]), pts[1], pts[-2]
        else:
            return sh, pts[1], pts[-2]

    w1, fp1, lp1 = wire_and_endpoints(e1)
    w2, fp2, lp2 = wire_and_endpoints(e2)
    w3 = w2.copy()

    line11 = Part.makeLine(fp1, fp2)
    line12 = Part.makeLine(lp1, lp2)
    line21 = Part.makeLine(fp1, lp2)
    line22 = Part.makeLine(lp1, fp2)
    d1 = line11.distToShape(line12)[0]
    d2 = line21.distToShape(line22)[0]
    # if (line21.Length + line22.Length) < (line11.Length + line12.Length):
    if d1 < d2:
        w3.reverse()
    # print(w1, w3)
    try:
        ruled = Part.makeRuledSurface(path=w1, profile=w3, orientation=1)
    except TypeError:
        ruled = Part.makeRuledSurface(w1, w3)
    if normalize:
        faces = []
        for f in ruled.Faces:
            s = f.Surface
            u0, u1, v0, v1 = s.bounds()
            normalized_knots = [(k - u0) / (u1 - u0) for k in s.getUKnots()]
            s.setUKnots(normalized_knots)
            faces.append(s.toShape())
        if len(faces) == 1:
            return faces[0]
        else:
            return Part.Shell(faces)
    return ruled


def nb_pcurves(edge):
    """returns the number of Pcurves of this edge"""
    i = 0
    while edge.curveOnSurface(i):
        i += 1
    return i


def get_pcurves(edge, idx=-1):
    """returns all the Pcurves of this edge
    pcurve_list = get_pcurves(edge, idx=-1)
    each pcurve of the list is a tuple of 5 items :
    - curve 2d
    - surface
    - placement
    - first parameter
    - last parameter
    if idx is in [0,4], only this item of the tuple is returned"""
    pcurves = []
    i = 0
    pc = edge.curveOnSurface(i)
    if pc and idx >= 0 and idx < 6:
        pc = pc[idx]
    while pc:
        pcurves.append(pc)
        i += 1
        pc = edge.curveOnSurface(i)
        if pc and idx >= 0 and idx < 6:
            pc = pc[idx]
    return pcurves


def anim(obj, path, on_path=False, reverse=False, duration=1.0, samples=100):
    """
    Animate obj along path
    anim(obj, path, on_path=False, duration=1.0, samples=100)
    path must be an edge or a wire
    if on_path is True, the animation path is absolute
    else, the animation path is relative to current obj placement
    reverse : reverse path direction
    duration : animation duration in seconds
    samples : number of animation samples
    """
    from time import sleep
    import FreeCADGui
    pts = path.discretize(samples)
    if reverse:
        pts.reverse()
    rpts = [p - pts[0] for p in pts]
    if not on_path:
        origin = obj.Placement.Base
    else:
        origin = pts[0]
    for p in rpts:
        obj.Placement.Base = origin + p
        FreeCADGui.ActiveDocument.update()
        sleep(float(duration) / samples)


def is_equal(obj1, obj2, tol=1e-7):
    """Test equality of two objects, with tolerance
    bool = is_equal(obj1, obj2, tol=1e-7)
    obj1, obj2 can be of type:
    - float
    - int
    - Vector
    - Vector2d
    - list of the above types"""
    if isinstance(obj1, (list, tuple)):
        equal = True
        for o1, o2 in zip(obj1, obj2):
            res = is_equal(o1, o2, tol)
            equal = equal and res
        return equal
    if isinstance(obj1, FreeCAD.Vector):
        return obj1.isEqual(obj2, tol)
    if isinstance(obj1, FreeCAD.Base.Vector2d):
        v1 = FreeCAD.Vector(obj1.x, obj1.y, 0)
        v2 = FreeCAD.Vector(obj2.x, obj2.y, 0)
        return v1.isEqual(v2, tol)
    if isinstance(obj1, float):
        return abs(obj1 - obj2) < tol
    else:
        return obj1 == obj2


def have_equal_property(geom1, geom2, prop, tol=1e-7):
    """Test equality of property prop of two geometries
    bool = have_equal_property(geom1, geom2, prop, tol=1e-7)
    Input :
    - geom1, geom2 (Part.Geometry): the two curves or surfaces to test
    - prop (string): the name of the property to test
    - tol (float): equality tolerance"""
    attr1 = getattr(geom1, prop)
    attr2 = getattr(geom2, prop)
    try:
        val1 = attr1()
        val2 = attr2()
        return is_equal(val1, val2, tol)
    except TypeError:  # They're not callable
        return is_equal(attr1, attr2, tol)


def geom_equal(geom1, geom2, tol=1e-7):
    """Test equality between two geometries
    by comparing their defining properties
    bool = geom_equal(geom1, geom2, tol=1e-7)
    geom1 and geom2 must be of type Part.Curve or Part.Surface"""
    if not geom1.TypeId == geom2.TypeId:
        return False
    curve_properties = ["FirstParameter", "LastParameter"]
    conic_properties = curve_properties + ["Location", "AngleXU", "Axis", "XAxis", "YAxis"]

    test_properties = dict()
    test_properties[Part.Point] = ["X", "Y", "Z"]
    test_properties[FreeCAD.Base.Vector] = ["x", "y", "z"]
    test_properties[FreeCAD.Base.Vector2d] = ["x", "y"]
    # Curves
    test_properties[Part.Line] = curve_properties + ["Location", "Direction"]
    test_properties[Part.Circle] = conic_properties + ["Radius"]
    test_properties[Part.Ellipse] = conic_properties + ["Focal", "Focus1", "Focus2", "MajorRadius", "MinorRadius"]
    test_properties[Part.Hyperbola] = conic_properties + ["Focal", "Focus1", "Focus2", "MajorRadius", "MinorRadius"]
    test_properties[Part.Parabola] = conic_properties + ["Focal", "Focus"]
    test_properties[Part.LineSegment] = test_properties[Part.Line]
    test_properties[Part.ArcOfCircle] = test_properties[Part.Circle]
    test_properties[Part.ArcOfEllipse] = test_properties[Part.Ellipse]
    test_properties[Part.ArcOfHyperbola] = test_properties[Part.Hyperbola]
    test_properties[Part.ArcOfParabola] = test_properties[Part.Parabola]
# BasisCurve is not implemented
#    test_properties[Part.OffsetCurve] = ["BasisCurve", "OffsetDirection", "OffsetValue"]
#    test_properties[Part.TrimmedCurve] = ["BasisCurve", "OffsetDirection", "OffsetValue"]
    test_properties[Part.BezierCurve] = curve_properties + ["Degree", "NbPoles", "getPoles", "getWeights"]
    test_properties[Part.BSplineCurve] = test_properties[Part.BezierCurve] + ["NbKnots", "KnotSequence"]
    # Surfaces
    test_properties[Part.Plane] = ["Axis", "Position"]
    test_properties[Part.Cone] = ["Apex", "Axis", "Center", "Radius", "SemiAngle"]
    test_properties[Part.Cylinder] = ["Axis", "Center", "Radius"]
    test_properties[Part.Sphere] = ["Axis", "Center", "Radius"]
    test_properties[Part.Toroid] = ["Axis", "Center", "MajorRadius", "MinorRadius"]
    test_properties[Part.BezierSurface] = ["UDegree", "VDegree", "NbUPoles", "NbVPoles", "getPoles", "getWeights"]
    test_properties[Part.BSplineSurface] = test_properties[Part.BezierSurface] + ["getUKnots", "getVKnots", "getUMultiplicities", "getVMultiplicities"]
    test_properties[Part.OffsetSurface] = ["BasisSurface", "OffsetValue"]
    test_properties[Part.SurfaceOfExtrusion] = ["BasisCurve", "Direction"]
    test_properties[Part.SurfaceOfRevolution] = ["BasisCurve", "Direction", "Location"]

    for prop in test_properties[geom1.__class__]:
        if not have_equal_property(geom1, geom2, prop, tol):
            return False
    return True

