# -*- coding: utf-8 -*-

__title__ = "Constrained Profile"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates an editable interpolation curve"

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
import profile_editor
reload(profile_editor)

TOOL_ICON = _utils.iconsPath() + '/editableSpline.svg'
#debug = _utils.debug
#debug = _utils.doNothing

#App::PropertyBool
#App::PropertyBoolList
#App::PropertyFloat
#App::PropertyFloatList
#App::PropertyFloatConstraint
#App::PropertyQuantity
#App::PropertyQuantityConstraint
#App::PropertyAngle
#App::PropertyDistance
#App::PropertyLength
#App::PropertySpeed
#App::PropertyAcceleration
#App::PropertyForce
#App::PropertyPressure
#App::PropertyInteger
#App::PropertyIntegerConstraint
#App::PropertyPercent
#App::PropertyEnumeration
#App::PropertyIntegerList
#App::PropertyIntegerSet
#App::PropertyMap
#App::PropertyString
#App::PropertyUUID
#App::PropertyFont
#App::PropertyStringList
#App::PropertyLink
#App::PropertyLinkSub
#App::PropertyLinkList
#App::PropertyLinkSubList
#App::PropertyMatrix
#App::PropertyVector
#App::PropertyVectorList
#App::PropertyPlacement
#App::PropertyPlacementLink
#App::PropertyColor
#App::PropertyColorList
#App::PropertyMaterial
#App::PropertyPath
#App::PropertyFile
#App::PropertyFileIncluded
#App::PropertyPythonObject
#Part::PropertyPartShape
#Part::PropertyGeometryList
#Part::PropertyShapeHistory
#Part::PropertyFilletEdges
#Sketcher::PropertyConstraintList

def midpoint(e):
    p = e.FirstParameter + 0.5 * (e.LastParameter - e.FirstParameter)
    return(e.valueAt(p))

class GordonProfileFP:
    """Creates an editable interpolation curve"""
    def __init__(self, obj, s, d, t):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Support",         "Profile", "Constraint shapes").Support = s
        obj.addProperty("App::PropertyFloatConstraint","Parametrization", "Profile", "Parametrization factor")
        obj.addProperty("App::PropertyFloat",       "Tolerance",       "Profile", "Tolerance").Tolerance = 1e-5
        obj.addProperty("App::PropertyBool",        "Periodic",        "Profile", "Periodic curve").Periodic = False
        obj.addProperty("App::PropertyVectorList",  "Data",            "Profile", "Data list").Data = d
        obj.addProperty("App::PropertyVectorList",  "Tangents",        "Profile", "Tangents list")
        obj.addProperty("App::PropertyBoolList",    "Flags",           "Profile", "Tangent flags")
        obj.addProperty("App::PropertyIntegerList", "DataType",        "Profile", "Types of interpolated points").DataType = t
        obj.addProperty("App::PropertyBoolList",    "LinearSegments",  "Profile", "Linear segment flags")
        obj.Parametrization = ( 1.0, 0.0, 1.0, 0.05 )
        obj.Proxy = self

    def onDocumentRestored(self, fp):
        fp.Parametrization = ( 1.0, 0.0, 1.0, 0.05 )

    def get_shapes(self, fp):
        if hasattr(fp,'Support'):
            sl = list()
            for ob,names in fp.Support:
                for name in names:
                    if   ("Vertex" in name):
                        n = eval(name.lstrip("Vertex"))
                        if len(ob.Shape.Vertexes) >= n:
                            sl.append(ob.Shape.Vertexes[n-1])
                    elif ("Edge" in name):
                        n = eval(name.lstrip("Edge"))
                        if len(ob.Shape.Edges) >= n:
                            sl.append(ob.Shape.Edges[n-1])
                    elif ("Face" in name):
                        n = eval(name.lstrip("Face"))
                        if len(ob.Shape.Faces) >= n:
                            sl.append(ob.Shape.Faces[n-1])
            return(sl)

    def get_points(self, fp, stretch=True):
        touched = False
        shapes = self.get_shapes(fp)
        if   not len(fp.Data) == len(fp.DataType):
            FreeCAD.Console.PrintError("Gordon Profile : Data and DataType mismatch\n")
            return(None)
        pts = list()
        shape_idx = 0
        for i in range(len(fp.Data)):
            if   fp.DataType[i] == 0: # Free point
                pts.append(fp.Data[i])
            elif (fp.DataType[i] == 1):
                if (shape_idx < len(shapes)): # project on shape
                    d,p,i = Part.Vertex(fp.Data[i]).distToShape(shapes[shape_idx])
                    if d > fp.Tolerance:
                        touched = True
                    pts.append(p[0][1]) #shapes[shape_idx].valueAt(fp.Data[i].x))
                    shape_idx += 1
                else:
                    pts.append(fp.Data[i])
        if stretch and touched:
            params = [0]
            knots = [0]
            moves = [pts[0]-fp.Data[0]]
            lsum = 0
            mults = [2]
            for i in range(1,len(pts)):
                lsum += fp.Data[i-1].distanceToPoint(fp.Data[i])
                params.append(lsum)
                if fp.DataType[i] == 1:
                    knots.append(lsum)
                    moves.append(pts[i]-fp.Data[i])
                    mults.insert(1,1)
            mults[-1] = 2
            if len(moves) < 2:
                return(pts)
            #FreeCAD.Console.PrintMessage("%s\n%s\n%s\n"%(moves,mults,knots))
            curve = Part.BSplineCurve()
            curve.buildFromPolesMultsKnots(moves,mults,knots,False,1)
            for i in range(1,len(pts)):
                if fp.DataType[i] == 0:
                    #FreeCAD.Console.PrintMessage("Stretch %s #%d: %s to %s\n"%(fp.Label,i,pts[i],curve.value(params[i])))
                    pts[i] += curve.value(params[i])
        if touched:
            return(pts)
        else:
            return(False)

    def execute(self, obj):
        pts = self.get_points(obj)
        if pts:
            if len(pts) < 2:
                FreeCAD.Console.PrintError("%s : Not enough points\n"%obj.Label)
                return(False)
            else:
                obj.Data = pts
        else:
            pts = obj.Data

        tans = [FreeCAD.Vector()]*len(pts)
        flags = [False]*len(pts)
        for i in range(len(obj.Tangents)):
            tans[i] = obj.Tangents[i]
        for i in range(len(obj.Flags)):
            flags[i] = obj.Flags[i]
        #if not (len(obj.LinearSegments) == len(pts)-1):
            #FreeCAD.Console.PrintError("%s : Points and LinearSegments mismatch\n"%obj.Label)
        if len(obj.LinearSegments) > 0:
            for i,b in enumerate(obj.LinearSegments):
                if b:
                    tans[i] = pts[i+1]-pts[i]
                    tans[i+1] = tans[i]
                    flags[i] = True
                    flags[i+1] = True
        params = profile_editor.parameterization(pts,obj.Parametrization,obj.Periodic)
        curve = Part.BSplineCurve()
        curve.interpolate(Points=pts, Parameters=params, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Tangents=tans, TangentFlags=flags)
        obj.Shape = curve.toShape()

    def onChanged(self, fp, prop):
        if prop in ("Support","Data","DataType","Periodic"):
            #FreeCAD.Console.PrintMessage("%s : %s changed\n"%(fp.Label,prop))
            if (len(fp.Data)==len(fp.DataType)) and (sum(fp.DataType)==len(fp.Support)):
                new_pts = self.get_points(fp, True)
                if new_pts:
                    fp.Data = new_pts
        if prop == "Parametrization":
            self.execute(fp)

    def onDocumentRestored(self, fp):
        fp.setEditorMode("Data", 2)
        fp.setEditorMode("DataType", 2)

class GordonProfileVP:
    def __init__(self,vobj):
        vobj.Proxy = self
        self.select_state = True
        self.active = False
        
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ip = None

    def setEdit(self,vobj,mode=0):
        if mode == 0:
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
            pts = list()
            sl = list()
            for ob,names in self.Object.Support:
                for name in names:
                    sl.append((ob,(name,)))
            shape_idx = 0
            for i in range(len(self.Object.Data)):
                p = self.Object.Data[i]
                t = self.Object.DataType[i]
                if t == 0:
                    pts.append(profile_editor.MarkerOnShape([p]))
                elif t == 1:
                    pts.append(profile_editor.MarkerOnShape([p],sl[shape_idx]))
                    shape_idx += 1
            for i in range(len(pts)): #p,t,f in zip(pts, self.Object.Tangents, self.Object.Flags):
                if i < min(len(self.Object.Flags),len(self.Object.Tangents)):
                    if self.Object.Flags[i]:
                        pts[i].tangent = self.Object.Tangents[i]
            self.ip = profile_editor.InterpoCurveEditor(pts, self.Object)
            self.ip.periodic = self.Object.Periodic
            self.ip.param_factor = self.Object.Parametrization
            for i in range(min(len(self.Object.LinearSegments),len(self.ip.lines))):
                self.ip.lines[i].tangent = self.Object.LinearSegments[i]
                self.ip.lines[i].updateLine()
            self.active = True
            return(True)
        return(False)

    def unsetEdit(self,vobj,mode=0):
        if isinstance(self.ip,profile_editor.InterpoCurveEditor):
            pts = list()
            typ = list()
            tans = list()
            flags = list()
            #original_links = self.Object.Support
            new_links = list()
            for p in self.ip.points:
                if isinstance(p,profile_editor.MarkerOnShape):
                    pt = p.points[0]
                    pts.append(FreeCAD.Vector(pt[0],pt[1],pt[2]))
                    if p.sublink:
                        new_links.append(p.sublink)
                        typ.append(1)
                    else:
                        typ.append(0)
                    if p.tangent:
                        tans.append(p.tangent)
                        flags.append(True)
                    else:
                        tans.append(FreeCAD.Vector())
                        flags.append(False)
            self.Object.Tangents = tans
            self.Object.Flags = flags
            self.Object.LinearSegments = [l.linear for l in self.ip.lines]
            self.Object.DataType = typ
            self.Object.Data = pts
            self.Object.Support = new_links
            vobj.Selectable = self.select_state
            self.ip.quit()
        self.ip = None
        self.active = False
        return(True)

    def doubleClicked(self,vobj):
        if not hasattr(self,'active'):
            self.active = False
        if not self.active:
            self.active = True
            #self.setEdit(vobj)
            vobj.Document.setEdit(vobj)
        else:
            vobj.Document.resetEdit()
            self.active = False
        return(True)

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class GordonProfileCommand:
    """Creates a editable interpolation curve"""
    docu = """*** Interpolation curve control keys :\n
    a - Select all / Deselect
    i - Insert point
    g - Grab objects
    t - Set / unset tangent (view direction)
    p - Align selected objects
    s - Snap points on shape / Unsnap
    l - Set/unset a linear interpolation
    x,y,z - Axis constraints during grab
    q - Apply changes and quit editing\n"""
    
    def makeFeature(self, sub, pts, typ):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Gordon Profile")
        proxy = GordonProfileFP(fp,sub,pts,typ)
        GordonProfileVP(fp.ViewObject)
        FreeCAD.Console.PrintMessage(GordonProfileCommand.docu)
        FreeCAD.ActiveDocument.recompute()
        fp.ViewObject.Document.setEdit(fp.ViewObject)
        
    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        try:
            ordered = FreeCADGui.activeWorkbench().Selection
            if ordered:
                s = ordered
        except AttributeError:
            pass

        sub = list()
        pts = list()
        typ = list()
        for obj in s:
            if obj.HasSubObjects:
                #FreeCAD.Console.PrintMessage("object has subobjects %s\n"%str(obj.SubElementNames))
                for n in obj.SubElementNames:
                    sub.append((obj.Object,[n]))
                for p in obj.PickedPoints:
                    pts.append(p)
                    
        if len(pts) == 0:
            pts = [FreeCAD.Vector(0,0,0),FreeCAD.Vector(0.5,0,0),FreeCAD.Vector(1,0,0)]
            typ = [0,0,0]
        elif len(pts) == 1:
            pts.append(pts[0]+FreeCAD.Vector(0.5,0,0))
            pts.append(pts[0]+FreeCAD.Vector(1,0,0))
            typ = [1,0,0]
        else:
            typ = [1]*len(pts)
        self.makeFeature(sub,pts,typ)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': __title__, 'ToolTip': __doc__}

FreeCADGui.addCommand('gordon_profile', GordonProfileCommand())
