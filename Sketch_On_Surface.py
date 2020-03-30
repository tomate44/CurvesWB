# -*- coding: utf-8 -*-

__title__ = "Sketch on surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Map a sketch on a surface"

import FreeCAD
import FreeCADGui
import Part
import Sketcher
from FreeCAD import Base
import _utils

TOOL_ICON = _utils.iconsPath() + '/sketch_surf.svg'
debug = _utils.debug
#debug = _utils.doNothing
vec = FreeCAD.Vector

## create a circular face
#circle=Part.makeCircle(4,App.Vector(5,5,0))
#face=Part.Face(Part.Wire(circle.Edges))
#Part.show(face)

## get the pcurve of the boundary edge of the face
#curve=face.curveOnSurface(face.Edges[0]) # curve is a tuple or none!

## convert the face to a nurbs and modify it
#nurbs_face = face.toNurbs()
#nurbs_surf = nurbs_face.Faces[0].Surface
#nurbs_surf.setPole(1,1,App.Vector(0,0,5))

## create a new edge from the pcurve with the modified nurbs
#edge = curve[0].toShape(nurbs_surf)

## create a new face from the nurbs and the new boundary edge
#face=Part.Face(nurbs_surf,Part.Wire([edge]))
#Part.show(face)

#skedges = [i.toShape() for i in obj.Geometry]
#comp = Part.Compound(skedges)
#comp.BoundBox
## BoundBox (10.2788, 10.7348, 0, 101.203, 71.9788, 0)

#Draft.scale([FreeCAD.ActiveDocument.Sketch],delta=FreeCAD.Vector(0.5,1.0,1.0),center=FreeCAD.Vector(3.91884532988,4.14834510717,7.07470992358),copy=True)


def Points2D(pts):
    if isinstance(pts,FreeCAD.Vector):
        return Base.Vector2d(pts.x,pts.y)
    elif isinstance(pts,(list,tuple)):
        l = [Points2D(p) for p in pts]
        return l
    else:
        App.Console.PrintError("Failed to convert points to 2D\n")
        return None

def toShape(curves2d,surf, Approx = 32):
    edges = []
    for c in curves2d:
        if Approx:
            pts = c.toShape(surf).discretize(QuasiNumber = Approx)
            bs = Part.BSplineCurve()
            bs.approximate(pts)
            edges.append(bs.toShape())
        else:
            edges.append(c.toShape(surf))
    com = Part.Compound(edges)
    return com

def to2D(geom):
    if isinstance(geom,list):
        r = []
        for e in geom:
            if isinstance(e,Part.Line):
                ls = Part.LineSegment(e.valueAt(e.FirstParameter),e.valueAt(e.LastParameter))
                r.append(to2D(ls))
            else:
                r.append(to2D(e))
        return r
    if isinstance(geom,Part.ArcOfCircle):
        debug('Arc Of Circle')
        
        circle2D = Part.Geom2d.Circle2d( Points2D(geom.Circle.Center), geom.Circle.Radius)
        curve2D = Part.Geom2d.ArcOfCircle2d( circle2D, geom.FirstParameter, geom.LastParameter)
        
    #elif isinstance(geom,Part.ArcOfConic):
        #print('Arc Of Conic')
    elif isinstance(geom,Part.ArcOfEllipse):
        debug('Arc Of Ellipse')
    elif isinstance(geom,Part.ArcOfHyperbola):
        debug('Arc Of Hyperbola')
    elif isinstance(geom,Part.ArcOfParabola):
        debug('Arc Of Parabola')
    elif isinstance(geom,Part.BSplineCurve):
        debug('BSpline Curve')

        poles3D = geom.getPoles()
        weights = geom.getWeights()
        knots =   geom.getKnots()
        mults =   geom.getMultiplicities()
        degree =  geom.Degree
        periodic  = geom.isPeriodic()

        poles2D = Points2D(poles3D)
        curve2D = Part.Geom2d.BSplineCurve2d()
        # buildFromPolesMultsKnots arguments: poles (sequence of Base.Vector), [mults , knots, periodic, degree, weights (sequence of float), CheckRational]
        curve2D.buildFromPolesMultsKnots( poles2D, mults, knots, periodic, degree, weights)

    elif isinstance(geom,Part.BezierCurve):
        debug('Bezier Curve')
        
        poles3D = geom.getPoles()
        weights = geom.getWeights()
        degree =  geom.Degree
        periodic  = geom.isPeriodic()

        poles2D = Points2D(poles3D)
        curve2D = Part.Geom2d.BezierCurve2d()
        curve2D.increase(degree)
        for i in range(geom.NbPoles):
            curve2D.setPole(i+1,poles2D[i])
            curve2D.setWeight(i+1,weights[i])
        
    elif isinstance(geom,Part.Circle):
        debug('Circle')
        
        curve2D = Part.Geom2d.Circle2d( Points2D(geom.Center), geom.Radius)
        
    #elif isinstance(geom,Part.Conic):
        #print('Conic')
    elif isinstance(geom,Part.Ellipse):
        debug('Ellipse')
        
        curve2D = Part.Geom2d.Ellipse2d( Points2D(geom.Center), geom.MajorRadius, geom.MinorRadius)
        
    elif isinstance(geom,Part.Hyperbola):
        debug('Hyperbola')
    elif isinstance(geom,Part.Parabola):
        debug('Parabola')
    elif isinstance(geom,Part.Line):
        debug('Line')
    elif isinstance(geom,Part.LineSegment):
        debug('LineSegment')
        
        p0 = geom.StartPoint
        p1 = geom.EndPoint
        Pts2D = Points2D([p0,p1])
        curve2D = Part.Geom2d.Line2dSegment(Pts2D[0],Pts2D[1])

    #print(curve2D)
    return curve2D

class sketchOnSurface:
    "This feature object maps a sketch on a surface"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub", "Face",   "SketchOnSurface", "Input face")
        obj.addProperty("App::PropertyLink",    "Sketch", "SketchOnSurface", "Input Sketch")
        obj.addProperty("App::PropertyBool",    "ConstructionBounds", "SketchOnSurface", "include construction geometry in sketch bounds").ConstructionBounds = True
        #obj.addProperty("App::PropertyBool",    "Scale",  "SketchOnSurface", "Scale sketch geometries").Scale = True
        obj.addProperty("App::PropertyBool",    "Fill",   "SketchOnSurface", "Fill face").Fill = False
        obj.addProperty("App::PropertyFloat",   "Inset",  "SketchOnSurface", "Fill face").Inset = 0.0
        obj.addProperty("App::PropertyFloat",   "Outset", "SketchOnSurface", "Fill face").Outset = 0.0
        obj.Proxy = self

    def mapping(self, obj, quad, face):
        proj = quad.project(obj.Sketch.Shape.Edges)
        new_edges = []
        for e in proj.Edges:
            try:
                c2d, fp, lp = quad.curveOnSurface(e)
                ne = c2d.toShape(face.Surface, fp, lp)
                new_edges.append(ne)
            except TypeError:
                debug("Failed to get 2D curve")
        sorted_edges = Part.sortEdges(new_edges)
        shapes = []
        for el in sorted_edges:
            w = Part.Wire(el)
            if obj.Fill and w.isClosed():
                f = Part.Face(face.Surface, w)
                f.validate()
                shapes.append(f)
            else:
                shapes.append(w)
        return shapes

    def execute(self, obj):
        if not obj.Sketch:
            debug("No Sketch")
            return
        #if obj.ConstructionBounds:
        skedges = []
        for i in obj.Sketch.Geometry:
            if i.Construction and not obj.ConstructionBounds:
                continue
            try:
                skedges.append(i.toShape())
            except:
                print("toShape() error, ignoring geometry")
        comp = Part.Compound(skedges)

        bb = comp.BoundBox
        u0, u1, v0, v1 = (bb.XMin,bb.XMax,bb.YMin,bb.YMax)
        debug("Sketch bounds = {}".format((u0, u1, v0, v1)))
        
        if not obj.Face:
            debug("No Face")
            return
        else:
            n = eval(obj.Face[1][0].lstrip('Face'))
            face = obj.Face[0].Shape.Faces[n-1]
            face.Placement = obj.Face[0].getGlobalPlacement()
        #s0, s1, t0, t1 = face.Surface.bounds() # Full surface
        s0, s1, t0, t1 = face.ParameterRange # or trimmed face ?
        debug("Target face bounds = {}".format((s0, s1, t0, t1)))
        
        bs = Part.BSplineSurface()
        poles = [[FreeCAD.Vector(u0,v0,0), FreeCAD.Vector(u0,v1,0)],
                 [FreeCAD.Vector(u1,v0,0), FreeCAD.Vector(u1,v1,0)]]
        umults = [2, 2]
        vmults = [2, 2]
        uknots = [s0, s1]
        vknots = [t0, t1]
        bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots, False, False, 1, 1)
        quad = bs.toShape()
        quad.Placement = obj.Sketch.getGlobalPlacement()
        shapes = []
        if (not hasattr(obj,'Inset') or not hasattr(obj,'Outset')):
            shapes = self.mapping(obj, quad, face)
        elif (obj.Inset == 0) and (obj.Outset == 0):
            shapes = self.mapping(obj, quad, face)
        else:
            if (obj.Inset > 0):
                f1 = face.makeOffsetShape(-obj.Inset, 1e-3)
                sh1 = self.mapping(obj, quad, f1.Face1)
            else:
                sh1 = self.mapping(obj, quad, face)
            if (obj.Outset > 0):
                f2 = face.makeOffsetShape(obj.Outset, 1e-3)
                sh2 = self.mapping(obj, quad, f2.Face1)
            else:
                sh2 = self.mapping(obj, quad, face)
            if obj.Fill:
                for i in range(len(sh1)):
                    loft = Part.makeLoft([sh1[i].Wires[0], sh2[i].Wires[0]], obj.Fill, True)
                    shapes.append(loft)
            else:
                shapes = sh1+sh2

        if shapes:
            obj.Shape = Part.Compound(shapes)

        

    def getSketchBounds(self, obj):
        if not obj.Sketch:
            debug("No Sketch")
            return
        else:
            if obj.ConstructionBounds:
                skedges = []
                for i in obj.Sketch.Geometry:
                    try:
                        skedges.append(i.toShape())
                    except:
                        print("toShape() error, ignoring geometry")
                #skedges = [i.toShape() for i in obj.Sketch.Geometry]
                comp = Part.Compound(skedges)
                bb = comp.BoundBox
                self.sketchBounds = (bb.XMin,bb.XMax,bb.YMin,bb.YMax)
                debug("Sketch bounds = %s"%str(self.sketchBounds))
            else:
                comp = Part.Compound(obj.Sketch.Shape.Edges)
                bb = comp.BoundBox
                self.sketchBounds = (bb.XMin,bb.XMax,bb.YMin,bb.YMax)
                debug("Sketch bounds = %s"%str(self.sketchBounds))

    def updateFace(self, obj):
        if not obj.Face:
            debug("No Face")
            return
        else:
            n = eval(obj.Face[1][0].lstrip('Face'))
            self.face = obj.Face[0].Shape.Faces[n-1]
            self.surface = self.face.Surface
            debug("Face update : %s"%str(obj.Face))
            return obj.Face[0].Shape.Faces[n-1]

    def getSurfaceBounds(self, obj):
        # Some surfaces have infinite dimensions (planes, cylinders)
        #self.surfaceBounds = self.surface.bounds()
        # Let's use face parameter range for now
        self.surfaceBounds = self.face.ParameterRange
        debug("Surface bounds = %s"%str(self.surfaceBounds))

    def scaleGeom(self, bs):
        pts = bs.getPoles()
        scpts = []
        for p in pts:
            v = p.sub(self.offset)
            v.scale(self.scale.x, self.scale.y, self.scale.z)
            scpts.append(self.offset.add(v))
        for i in range(bs.NbPoles):
            bs.setPole(i+1,scpts[i])
        return bs

    def scaleSketch(self, obj):
        sketchRangeX  = self.sketchBounds[1] - self.sketchBounds[0]
        sketchRangeY  = self.sketchBounds[3] - self.sketchBounds[2]
        surfaceRangeX = self.surfaceBounds[1] - self.surfaceBounds[0]
        surfaceRangeY = self.surfaceBounds[3] - self.surfaceBounds[2]
        scaleX = surfaceRangeX / sketchRangeX
        scaleY = surfaceRangeY / sketchRangeY
        self.scale = FreeCAD.Vector(scaleX, scaleY, 1.0)
        offsetX = self.surfaceBounds[0] - self.sketchBounds[0]
        offsetY = self.surfaceBounds[2] - self.sketchBounds[2]
        self.offset = FreeCAD.Vector(offsetX, offsetY, 0.0)
        #self.scaledSketch = Draft.scale([obj.Sketch],delta=sc,center=off,copy=True)
        self.geoms = []
        for g in obj.Sketch.Geometry:
            if hasattr(g,'Construction'):
                if not g.Construction:
                    try:
                        bs = g.toBSpline()
                    except AttributeError:
                        debug("Failed to convert %s to BSpline"%str(g))
                    if hasattr(obj,'Scale'):
                        if obj.Scale:
                            sbs = self.scaleGeom(bs)
                            self.geoms.append(sbs)
                        else:
                            self.geoms.append(bs)
                    else:
                        self.geoms.append(bs)


    def mapOnSurface(self, obj):
        #for e in self.scaledSketch.Shape.Edges
        c2d = to2D(self.geoms)
        debug("to2D : %s"%str(c2d))
        compound = toShape(c2d,self.surface, Approx = False)
        compound.connectEdgesToWires(False, 1e-7)
        if hasattr(obj,'Fill'):
            if not obj.Fill:
                if compound.Edges:
                    obj.Shape = compound
            else:
                outer = compound.Wires[0]
                outer.fixWire()
                inner = []
                for w in compound.Wires[1:]:
                    w.fixWire()
                    if w.BoundBox.DiagonalLength > outer.BoundBox.DiagonalLength:
                        inner.append(outer)
                        outer = w
                    else:
                        inner.append(w)
                of = Part.Face(self.surface,outer)
                of.validate()
                nf = of.copy()
                for w in inner:
                    nf = Part.Face(nf.copy(),w)
                    nf.validate()
                try:
                    nf.check()
                    obj.Shape = nf
                except:
                    if compound.Edges:
                        obj.Shape = compound
                    FreeCAD.Console.PrintError("Failed to create face\n")
                    
        return

    def execute2(self, obj):
        if not obj.Sketch:
            debug("No Sketch")
            return
        if not "Restore" in obj.State:
            debug("***** execute *****")
            self.getSketchBounds(obj)
            self.updateFace(obj)
            self.getSurfaceBounds(obj)
            self.scaleSketch(obj)
            self.mapOnSurface(obj)
            debug("----- execute -----")

    def onChanged(self, fp, prop):
        pass
        #if prop == "Sketch":
            ##self.getSketchBounds(fp)
            #return
        #if prop == "Face":
            #self.updateFace(fp)
            ##self.getSurfaceBounds(fp)
            #return
        #else:
            #debug("onChanged : %s -> %s"%(fp.Label,prop))
            #return
            
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

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
        
    #def onDelete(self, feature, subelements): # subelements is a tuple of strings
        #for c in self.children:
            #if hasattr(c,"ViewObject"):
                #c.ViewObject.Visibility = True
        #return True

def addFaceWireToSketch(fa, w, sk):
    curves = list()
    const = list()
    pl = Part.Plane()
    for idx in range(len(w.Edges)):
        e = fa.curveOnSurface(w.Edges[idx])
        e3d = e[0].toShape(pl)
        tc = e3d.Curve.trim(e[1],e[2])
        curves.append(tc)
    o = int(sk.GeometryCount)
    sk.addGeometry(curves,False)
    
    # Coincident constraints
    #ar = range(len(curves))+[0]
    #for idx in range(len(curves)):
        #const.append(Sketcher.Constraint('Coincident',o+idx,2,o+ar[idx+1],1))
    
    for idx in range(len(curves)):
        const.append(Sketcher.Constraint('Block',o+idx))
    sk.addConstraint(const)

def addFaceBoundsToSketch(fa, sk):
    geoList = list()
    conList = list()
    u0,u1,v0,v1 = fa.ParameterRange
    if isinstance(fa.Surface, Part.Cylinder):
        u1 *= fa.Surface.Radius
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
    addFaceBoundsToSketch(fa, sk)
    
    for w in fa.Wires:
        addFaceWireToSketch(fa, w, sk)
    
    for i in range(int(sk.GeometryCount)):
        sk.toggleConstruction(i)

class SoS:
    def Activated(self):
        sketchFound = False
        faceFound = False

        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.Object.TypeId == 'Sketcher::SketchObject':
                sketch = selobj.Object
                sketchFound = True
            elif selobj.HasSubObjects:
                if issubclass(type(selobj.SubObjects[0]),Part.Face):
                    face = (selobj.Object,[selobj.SubElementNames[0]])
                    fa = selobj.SubObjects[0]
                    faceFound = True
            else:
                if selobj.Object.Shape.Faces:
                    face = (selobj.Object,['Face1'])
                    faceFound = True

        if faceFound:
            doc = FreeCAD.ActiveDocument
            if not sketchFound:
                sketch = doc.addObject('Sketcher::SketchObject','Mapped_Sketch')
                build_sketch(sketch, fa)
            sos = doc.addObject("Part::FeaturePython","Sketch On Surface")
            sketchOnSurface(sos)
            sos.Sketch = sketch
            sosVP(sos.ViewObject)
            sos.Face = face
            doc.recompute()
            sketch.ViewObject.Visibility = False
            #if not sketchFound:
                #sos.ConstructionBounds = False
                #sos.Scale = False
        else:
            FreeCAD.Console.PrintMessage("Please select 1 face (in the 3D view) and optionally 1 sketch\n")

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('SoS', SoS())
        

