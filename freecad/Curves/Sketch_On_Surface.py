# -*- coding: utf-8 -*-

__title__ = "Sketch on surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Map a sketch on a surface"

import os
import FreeCAD
import FreeCADGui
import Part
import Sketcher
from FreeCAD import Base
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'sketch_surf.svg')

debug = _utils.debug
#debug = _utils.doNothing
vec = FreeCAD.Vector


# DEPRECATED

#def Points2D(pts):
    #if isinstance(pts,FreeCAD.Vector):
        #return Base.Vector2d(pts.x,pts.y)
    #elif isinstance(pts,(list,tuple)):
        #l = [Points2D(p) for p in pts]
        #return l
    #else:
        #App.Console.PrintError("Failed to convert points to 2D\n")
        #return None

#def toShape(curves2d,surf, Approx = 32):
    #edges = []
    #for c in curves2d:
        #if Approx:
            #pts = c.toShape(surf).discretize(QuasiNumber = Approx)
            #bs = Part.BSplineCurve()
            #bs.approximate(pts)
            #edges.append(bs.toShape())
        #else:
            #edges.append(c.toShape(surf))
    #com = Part.Compound(edges)
    #return com

#def to2D(geom):
    #if isinstance(geom,list):
        #r = []
        #for e in geom:
            #if isinstance(e,Part.Line):
                #ls = Part.LineSegment(e.valueAt(e.FirstParameter),e.valueAt(e.LastParameter))
                #r.append(to2D(ls))
            #else:
                #r.append(to2D(e))
        #return r
    #if isinstance(geom,Part.ArcOfCircle):
        #debug('Arc Of Circle')
        
        #circle2D = Part.Geom2d.Circle2d( Points2D(geom.Circle.Center), geom.Circle.Radius)
        #curve2D = Part.Geom2d.ArcOfCircle2d( circle2D, geom.FirstParameter, geom.LastParameter)
        
    ##elif isinstance(geom,Part.ArcOfConic):
        ##print('Arc Of Conic')
    #elif isinstance(geom,Part.ArcOfEllipse):
        #debug('Arc Of Ellipse')
    #elif isinstance(geom,Part.ArcOfHyperbola):
        #debug('Arc Of Hyperbola')
    #elif isinstance(geom,Part.ArcOfParabola):
        #debug('Arc Of Parabola')
    #elif isinstance(geom,Part.BSplineCurve):
        #debug('BSpline Curve')

        #poles3D = geom.getPoles()
        #weights = geom.getWeights()
        #knots =   geom.getKnots()
        #mults =   geom.getMultiplicities()
        #degree =  geom.Degree
        #periodic  = geom.isPeriodic()

        #poles2D = Points2D(poles3D)
        #curve2D = Part.Geom2d.BSplineCurve2d()
        ## buildFromPolesMultsKnots arguments: poles (sequence of Base.Vector), [mults , knots, periodic, degree, weights (sequence of float), CheckRational]
        #curve2D.buildFromPolesMultsKnots( poles2D, mults, knots, periodic, degree, weights)

    #elif isinstance(geom,Part.BezierCurve):
        #debug('Bezier Curve')
        
        #poles3D = geom.getPoles()
        #weights = geom.getWeights()
        #degree =  geom.Degree
        #periodic  = geom.isPeriodic()

        #poles2D = Points2D(poles3D)
        #curve2D = Part.Geom2d.BezierCurve2d()
        #curve2D.increase(degree)
        #for i in range(geom.NbPoles):
            #curve2D.setPole(i+1,poles2D[i])
            #curve2D.setWeight(i+1,weights[i])
        
    #elif isinstance(geom,Part.Circle):
        #debug('Circle')
        
        #curve2D = Part.Geom2d.Circle2d( Points2D(geom.Center), geom.Radius)
        
    ##elif isinstance(geom,Part.Conic):
        ##print('Conic')
    #elif isinstance(geom,Part.Ellipse):
        #debug('Ellipse')
        
        #curve2D = Part.Geom2d.Ellipse2d( Points2D(geom.Center), geom.MajorRadius, geom.MinorRadius)
        
    #elif isinstance(geom,Part.Hyperbola):
        #debug('Hyperbola')
    #elif isinstance(geom,Part.Parabola):
        #debug('Parabola')
    #elif isinstance(geom,Part.Line):
        #debug('Line')
    #elif isinstance(geom,Part.LineSegment):
        #debug('LineSegment')
        
        #p0 = geom.StartPoint
        #p1 = geom.EndPoint
        #Pts2D = Points2D([p0,p1])
        #curve2D = Part.Geom2d.Line2dSegment(Pts2D[0],Pts2D[1])

    ##print(curve2D)
    #return curve2D

def stretched_plane(poles, param_range=[0,2,0,2], extend_factor=1.0):
    s0, s1, t0, t1 = param_range
    bs = Part.BSplineSurface()
    umults = [2, 2]
    vmults = [2, 2]
    uknots = [s0, s1]
    vknots = [t0, t1]
    if extend_factor > 1.0:
        ur = s1 - s0
        vr = t1 - t0
        uknots = [s0 - extend_factor * ur, s1 + extend_factor * ur]
        vknots = [t0 - extend_factor * vr, t1 + extend_factor * vr]
        diag_1 = poles[1][1] - poles[0][0]
        diag_2 = poles[1][0] - poles[0][1]
        np1 = poles[0][0] - extend_factor * diag_1
        np2 = poles[0][1] - extend_factor * diag_2
        np3 = poles[1][0] + extend_factor * diag_2
        np4 = poles[1][1] + extend_factor * diag_1
        poles = [[np1,np2],[np3,np4]]
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots, False, False, 1, 1)
    return bs

class BoundarySorter:
    def __init__(self, wires, surface=None, only_closed=False):
        self.wires = []
        self.parents = []
        self.sorted_wires = []
        self.surface = surface
        for w in wires:
            if only_closed and not w.isClosed():
                debug("Skipping open wire")
                continue
            self.wires.append(w)
            self.parents.append([])
            self.sorted_wires.append([])
        self.done = False
    def fine_check_inside(self, w1, w2):
        if self.surface is not None:
            f = Part.Face(self.surface, w2)
        else:
            f = Part.Face(w2)
        if not f.isValid():
            f.validate()
        if f.isValid():
            pt = w1.Vertex1.Point
            u,v = f.Surface.parameter(pt)
            return f.isPartOfDomain(u,v)
        return False
    def check_inside(self):
        for i, w1 in enumerate(self.wires):
            for j, w2 in enumerate(self.wires):
                if not i == j:
                    if w2.BoundBox.isInside(w1.BoundBox):
                        if self.fine_check_inside(w1, w2):
                            self.parents[i].append(j)
    def sort_pass(self):
        to_remove = []
        for i,p in enumerate(self.parents):
            if (p is not None) and p == []:
                to_remove.append(i)
                self.sorted_wires[i].append(self.wires[i])
                self.parents[i] = None
        #print("Removing parents : {}".format(to_remove))
        for i,p in enumerate(self.parents):
            if (p is not None) and len(p) == 1:
                to_remove.append(i)
                self.sorted_wires[p[0]].append(self.wires[i])
                self.parents[i] = None
        #print("Removing full : {}".format(to_remove))
        if len(to_remove) > 0:
            for i,p in enumerate(self.parents):
                if (p is not None):
                    for r in to_remove:
                        if r in p:
                            p.remove(r)
        else:
            self.done = True
    def sort(self):
        self.check_inside()
        #print(self.parents)
        while not self.done:
            #print("Pass {}".format(i))
            self.sort_pass()
        result = []
        for w in self.sorted_wires:
            if w:
                result.append(w)
        return result

class sketchOnSurface:
    "This feature object maps a sketch on a surface"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink",    "Sketch", "SketchOnSurface", "Input Sketch")
        obj.addProperty("App::PropertyLinkList",    "ExtraObjects", "SketchOnSurface", "Additional objects that will be mapped on surface")
        obj.addProperty("App::PropertyBool",    "FillFaces",     "Settings", "Make faces from closed wires").FillFaces = False
        obj.addProperty("App::PropertyBool",    "FillExtrusion", "Settings", "Add extrusion faces").FillExtrusion = True
        obj.addProperty("App::PropertyFloat",   "Offset",   "Settings", "Offset distance of mapped sketch").Offset = 0.0
        obj.addProperty("App::PropertyFloat",   "Thickness","Settings", "Extrusion thickness").Thickness = 0.0
        obj.addProperty("App::PropertyBool",    "ReverseU", "Touchup", "Reverse U direction").ReverseU = False
        obj.addProperty("App::PropertyBool",    "ReverseV", "Touchup", "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool",    "SwapUV", "Touchup", "Swap U and V directions").ReverseV = False
        obj.addProperty("App::PropertyBool",    "ConstructionBounds", "Touchup", "include construction geometry in sketch bounds").ConstructionBounds = True
        obj.Proxy = self

    def force_closed_bspline2d(self, c2d):
        """Force close a 2D Bspline curve by moving last pole to first"""
        c2d.setPole(c2d.NbPoles, c2d.getPole(1))
        debug("Force closing 2D curve")

    def build_faces(self, wl, face):
        faces = []
        for w in wl:
            w.fixWire(face, 1e-7)
        bs = BoundarySorter(wl, face.Surface, True)
        for i, wirelist in enumerate(bs.sort()):
            #print(wirelist)
            f = Part.Face(face.Surface, wirelist[0])
            #f.sewShape()
            if not f.isValid():
                debug("{:3}:Invalid initial face".format(i))
                f.validate()
            if len(wirelist) > 1:
                f.cutHoles(wirelist[1:])
                f.validate()
            f.sewShape()
            if not f.isValid():
                debug("{:3}:Invalid final face".format(i))
            faces.append(f)
        return faces

    def map_shapelist(self, shapes, quad, face, fillfaces=False):
        shapelist = []
        for i,shape in enumerate(shapes):
            debug("mapping shape # {}".format(i+1))
            shapelist.extend(self.map_shape(shape, quad, face, fillfaces))
            debug("Total : {} shapes".format(len(shapelist)))
        return shapelist

    def map_shape(self, shape, quad, face, fillfaces=False):
        if not isinstance(shape, Part.Shape):
            return []
        #proj = quad.project(shape.Edges)
        new_edges = []
        for oe in shape.Edges:
            proj = quad.project([oe])
            for e in proj.Edges:
                c2d, fp, lp = quad.curveOnSurface(e)
                if oe.isClosed() and not c2d.isClosed():
                    self.force_closed_bspline2d(c2d)
                ne = c2d.toShape(face.Surface, fp, lp) # toShape produces 1e-5 tolerance
                #debug(ne.Placement)
                #debug(face.Placement)
                #ne.Placement = face.Placement
                vt = ne.getTolerance(1, Part.Vertex)
                et = ne.getTolerance(1, Part.Edge)
                if vt < et:
                    ne.fixTolerance(et, Part.Vertex)
                    #debug("fixing tolerance : {0:e} -> {1:e}".format(vt,et))
                new_edges.append(ne)
            #else: #except TypeError:
                #error("Failed to get 2D curve")
        sorted_edges = Part.sortEdges(new_edges)
        wirelist = [Part.Wire(el) for el in sorted_edges]
        if fillfaces:
            return self.build_faces(wirelist, face)
        else:
            return wirelist

    def execute(self, obj):
        def error(msg):
            func_name = "{} (Sketch_On_Surface)  : ".format(obj.Label)
            FreeCAD.Console.PrintError(func_name + msg + "\n")
        if not obj.Sketch:
            error("No Sketch attached")
            return
        skedges = []
        for i in obj.Sketch.Geometry:
            if i.Construction and obj.ConstructionBounds:
                skedges.append(i.toShape())
            elif not i.Construction and not obj.ConstructionBounds:
                skedges.append(i.toShape())
            #else:
                #debug("toShape() error, ignoring geometry")
        comp = Part.Compound(skedges)

        bb = comp.BoundBox
        u0, u1, v0, v1 = (bb.XMin,bb.XMax,bb.YMin,bb.YMax)
        debug("Sketch bounds = {}".format((u0, u1, v0, v1)))
        
        try:
            n = eval(obj.Sketch.Support[0][1][0].lstrip('Face'))
            face = obj.Sketch.Support[0][0].Shape.Faces[n-1]
            #face.Placement = obj.Sketch.Support[0][0].getGlobalPlacement()
        except (IndexError, AttributeError, SyntaxError) as e:
            error("Failed to get the face support of the sketch\n")
            return
        debug("Target face bounds = {}".format(face.ParameterRange))
        
        prange = face.ParameterRange
        if obj.ReverseU:
            u0, u1 = u1, u0
        if obj.ReverseV:
            v0, v1 = v1, v0
        if obj.SwapUV:
            #u0, u1, v0, v1 = v0, v1, u0, u1
            prange = face.ParameterRange[2:] + face.ParameterRange[:2]
        pts = [[FreeCAD.Vector(u0,v0,0), FreeCAD.Vector(u0,v1,0)],
               [FreeCAD.Vector(u1,v0,0), FreeCAD.Vector(u1,v1,0)]]
        bs = stretched_plane(pts, prange, 10.0)
        if obj.SwapUV:
            bs.exchangeUV()
        quad = bs.toShape()
        quad.Placement = obj.Sketch.getGlobalPlacement()
        imput_shapes = [obj.Sketch.Shape] + [o.Shape for o in obj.ExtraObjects]
        shapes_1 = []
        shapes_2 = []
        if (obj.Offset == 0):
            shapes_1 = self.map_shapelist(imput_shapes, quad, face, obj.FillFaces)
        else:
            f1 = face.makeOffsetShape(obj.Offset, 1e-3)
            shapes_1 = self.map_shapelist(imput_shapes, quad, f1.Face1, obj.FillFaces)
        if (obj.Thickness == 0):
            if shapes_1:
                obj.Shape = Part.Compound(shapes_1)
            return
        else:
            f2 = face.makeOffsetShape(obj.Offset+obj.Thickness, 1e-3)
            shapes_2 = self.map_shapelist(imput_shapes, quad, f2.Face1, obj.FillFaces)
            if not obj.FillExtrusion:
                if shapes_1 or shapes_2:
                    obj.Shape = Part.Compound(shapes_1 + shapes_2)
                    return
            else:
                shapes = []
                for i in range(len(shapes_1)):
                    if isinstance(shapes_1[i], Part.Face):
                        faces = shapes_1[i].Faces + shapes_2[i].Faces
                        #error_wires = []
                        for j in range(len(shapes_1[i].Edges)):
                            if obj.FillFaces and shapes_1[i].Edges[j].isSeam(shapes_1[i]):
                                continue
                            ruled = Part.makeRuledSurface(shapes_1[i].Edges[j], shapes_2[i].Edges[j])
                            faces.append(ruled)
                            #try:
                                #face_is_closed = False
                                #for ed in shapes_1[i].Wires[j].Edges:
                                    #if ed.isSeam(shapes_1[i]):
                                        #face_is_closed = True
                                        #debug("closed face detected")
                                #loft = Part.makeLoft([shapes_1[i].Wires[j], shapes_2[i].Wires[j]], False, True, face_is_closed, 5)
                                #faces.extend(loft.Faces)
                            #except Part.OCCError:
                                ##error_wires.extend([shapes_1[i].Wires[j], shapes_2[i].Wires[j]])
                                #FreeCAD.Console.PrintError("Sketch on surface : failed to create loft face ({},{})".format(i,j))
                        try:
                            shell = Part.Shell(faces)
                            shell.sewShape()
                            solid = Part.Solid(shell)
                            shapes.append(solid)
                        except Part.OCCError:
                            FreeCAD.Console.PrintWarning("Sketch on surface : failed to create solid #{}.\n".format(i+1))
                            shapes.extend(faces)
                    else:
                        ruled = Part.makeRuledSurface(shapes_1[i].Wires[0], shapes_2[i].Wires[0])
                        shapes.append(ruled)
                #shapes.append(quad)
                if shapes:
                    if len(shapes) == 1:
                        obj.Shape = shapes[0]
                    elif len(shapes) > 1:
                        obj.Shape = Part.Compound(shapes)


class sosVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        self.children = []
       
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        #self.ViewObject = vobj
        self.Object = vobj.Object
        #if self.Object.Sketch:
            #self.children = [self.Object.Sketch]
        #else:
            #self.children = []
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        return [self.Object.Sketch]
        
def addFaceWireToSketch(fa, w, sk):
    curves = list()
    const = list()
    pl = Part.Plane()
    for idx in range(len(w.Edges)):
        e,fp,lp = fa.curveOnSurface(w.Edges[idx])
        e3d = e.toShape(pl)
        tc = e3d.Curve.trim(fp, lp)
        curves.append(tc)
    o = int(sk.GeometryCount)
    sk.addGeometry(curves,False)
    
    for idx in range(len(curves)):
        const.append(Sketcher.Constraint('Block',o+idx))
    sk.addConstraint(const)

def addFaceBoundsToSketch(para_range, sk):
    geoList = list()
    conList = list()
    u0,u1,v0,v1 = para_range
    geoList.append(Part.LineSegment(vec(u0,v0,0),vec(u1,v0,0)))
    geoList.append(Part.LineSegment(vec(u1,v0,0),vec(u1,v1,0)))
    geoList.append(Part.LineSegment(vec(u1,v1,0),vec(u0,v1,0)))
    geoList.append(Part.LineSegment(vec(u0,v1,0),vec(u0,v0,0)))
    o = int(sk.GeometryCount)
    sk.addGeometry(geoList,False)
    
    conList.append(Sketcher.Constraint('Coincident',o+0,2,o+1,1))
    conList.append(Sketcher.Constraint('Coincident',o+1,2,o+2,1))
    conList.append(Sketcher.Constraint('Coincident',o+2,2,o+3,1))
    conList.append(Sketcher.Constraint('Coincident',o+3,2,o+0,1))
    conList.append(Sketcher.Constraint('Horizontal',o+0))
    conList.append(Sketcher.Constraint('Horizontal',o+2))
    conList.append(Sketcher.Constraint('Vertical',o+1))
    conList.append(Sketcher.Constraint('Vertical',o+3))
    conList.append(Sketcher.Constraint('DistanceX',o+2,2,o+2,1,u1-u0))
    conList.append(Sketcher.Constraint('DistanceY',o+1,1,o+1,2,v1-v0))
    conList.append(Sketcher.Constraint('DistanceX',o+0,1,-1,1,-u0)) 
    conList.append(Sketcher.Constraint('DistanceY',o+0,1,-1,1,-v0)) 
    sk.addConstraint(conList)

def build_sketch(sk, fa):
    # add the bounding box of the face to the sketch
    u0,u1,v0,v1 = fa.ParameterRange
    if isinstance(fa.Surface, Part.Cylinder):
        u0 *= fa.Surface.Radius
        u1 *= fa.Surface.Radius
        addFaceBoundsToSketch([u0,u1,v0,v1], sk)
    #elif isinstance(fa.Surface, Part.Cone):
        #u1 = 0.5 * (fa.Edge1.Length + fa.Edge3.Length)
        #addFaceBoundsToSketch([u0,u1,v0,v1], sk)
    #elif len(fa.Edges) == 4:
        #u1 = 0.5 * (fa.Edge1.Length + fa.Edge3.Length)
        #v1 = 0.5 * (fa.Edge2.Length + fa.Edge4.Length)
        #addFaceBoundsToSketch([0,u1,0,v1], sk)
    else:
        for w in fa.Wires:
            addFaceWireToSketch(fa, w, sk)
    
    for i in range(int(sk.GeometryCount)):
        sk.toggleConstruction(i)

class SoS:
    def get_selection(self):
        sketch = None
        face_link = []
        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.Object.TypeId == 'Sketcher::SketchObject':
                sketch = selobj.Object
            elif selobj.HasSubObjects:
                if issubclass(type(selobj.SubObjects[0]),Part.Face):
                    face_link = (selobj.Object,[selobj.SubElementNames[0]])
        return sketch, face_link

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sketch, face_link = self.get_selection()
        if not sketch and not face_link:
            FreeCAD.Console.PrintMessage("Please select a face (in the 3D view) or a sketch\n")
            return
        if not sketch:
            sketch = doc.addObject('Sketcher::SketchObject','Mapped_Sketch')
            sketch.Support = face_link
            n = eval(face_link[1][0].lstrip('Face'))
            fa = face_link[0].Shape.Faces[n-1]
            build_sketch(sketch, fa)
            doc.recompute()
        sos = doc.addObject("Part::FeaturePython","Sketch On Surface")
        sketchOnSurface(sos)
        sos.Sketch = sketch
        sosVP(sos.ViewObject)
        doc.recompute()
        sketch.ViewObject.Visibility = False

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('SoS', SoS())
        

