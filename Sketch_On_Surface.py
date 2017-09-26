from __future__ import division # allows floating point division from integers
import FreeCAD, Part, Draft
import os, dummy, FreeCADGui
from FreeCAD import Base

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

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

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")



def Points2D(pts):
    if isinstance(pts,FreeCAD.Vector):
        return Base.Vector2d(pts.x,pts.y)
    elif isinstance(pts,(list,tuple)):
        l = []
        for p in pts:
            l.append(Base.Vector2d(p.x,p.y))
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
    return(curve2D)


class sketchOnSurface:
    "This feature object maps a sketch on a surface"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSub", "Face",   "SketchOnSurface", "Input face")
        obj.addProperty("App::PropertyLink",    "Sketch", "SketchOnSurface", "Input Sketch")
        obj.addProperty("App::PropertyBool",    "ConstructionBounds", "SketchOnSurface", "include construction geometry in sketch bounds").ConstructionBounds = False
        obj.Proxy = self

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
                    bs = g.toBSpline()
                    sbs = self.scaleGeom(bs)
                    self.geoms.append(sbs)


    def mapOnSurface(self, obj):
        #for e in self.scaledSketch.Shape.Edges
        c2d = to2D(self.geoms)
        debug("to2D : %s"%str(c2d))
        compound = toShape(c2d,self.surface, Approx = False)
        obj.Shape = compound
        return

    def execute(self, obj):
        debug("***** execute *****")
        self.getSketchBounds(obj)
        self.updateFace(obj)
        self.getSurfaceBounds(obj)
        self.scaleSketch(obj)
        self.mapOnSurface(obj)
        debug("----- execute -----")

    def onChanged(self, fp, prop):
        
        if prop == "Sketch":
            #self.getSketchBounds(fp)
            return
        if prop == "Face":
            self.updateFace(fp)
            #self.getSurfaceBounds(fp)
            return
        else:
            debug("onChanged : %s -> %s"%(fp.Label,prop))
            return
            
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


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
                    faceFound = True

        if sketchFound & faceFound:
            doc = FreeCAD.ActiveDocument
            sos = doc.addObject("Part::FeaturePython","Sketch On Surface")
            sketchOnSurface(sos)
            sos.ViewObject.Proxy=0
            sos.Sketch = sketch
            sos.Face = face
            doc.recompute()
        else:
            FreeCAD.Console.PrintMessage("Please select exactly 1 face and 1 sketch\n")

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/sketch_surf.svg', 'MenuText': 'SoS', 'ToolTip': 'Maps a sketch on a surface'}

FreeCADGui.addCommand('SoS', SoS())
        

