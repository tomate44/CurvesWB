# -*- coding: utf-8 -*-

__title__ = "Interpolate"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Interpolate a set of points."

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/interpolate.svg'
debug = _utils.debug
#debug = _utils.doNothing


# ********************************************************
# **** Part.BSplineCurve.interpolate() documentation *****
# ********************************************************

#Replaces this B-Spline curve by interpolating a set of points.
#The function accepts keywords as arguments.

#interpolate(Points = list_of_points) 

#Optional arguments :

#PeriodicFlag = bool (False) : Sets the curve closed or opened.
#Tolerance = float (1e-6) : interpolating tolerance

#Parameters : knot sequence of the interpolated points.
#If not supplied, the function defaults to chord-length parameterization.
#If PeriodicFlag == True, one extra parameter must be appended.

#EndPoint Tangent constraints :

#InitialTangent = vector, FinalTangent = vector
#specify tangent vectors for starting and ending points 
#of the BSpline. Either none, or both must be specified.

#Full Tangent constraints :

#Tangents = list_of_vectors, TangentFlags = list_of_bools
#Both lists must have the same length as Points list.
#Tangents specifies the tangent vector of each point in Points list.
#TangentFlags (bool) activates or deactivates the corresponding tangent.
#These arguments will be ignored if EndPoint Tangents (above) are also defined.

#Note : Continuity of the spline defaults to C2. However, if periodic, or tangents 
#are supplied, the continuity will drop to C1.

class Interpolate:
    def __init__(self, obj , source):
        ''' Add the properties '''
        debug("\nInterpolate class Init\n")
        obj.addProperty("App::PropertyLinkSubList",    "PointList",      "General",    "Point list to interpolate").PointList = source
        obj.addProperty("App::PropertyBool",           "Periodic",       "General",    "Set the curve closed").Periodic = False
        obj.addProperty("App::PropertyFloat",          "Tolerance",      "General",    "Interpolation tolerance").Tolerance = 1e-7
        obj.addProperty("App::PropertyFloatList",      "Parameters",     "Parameters", "Parameters of interpolated points")
        obj.addProperty("App::PropertyEnumeration",    "Parametrization","Parameters", "Parametrization type").Parametrization=["ChordLength","Centripetal","Uniform","Custom"]
        obj.addProperty("App::PropertyVectorList",     "Tangents",       "Tangents",   "Weight of curve length for smoothing algorithm").LengthWeight=1.0
        obj.addProperty("App::PropertyBoolList",       "TangentFlags",   "Tangents",   "Weight of curve curvature for smoothing algorithm").CurvatureWeight=1.0
        obj.Proxy = self
        obj.Parametrization = "ChordLength"

    def setTolerance(self, obj):
        try:
            l = obj.PointObject.Shape.BoundBox.DiagonalLength
            obj.ApproxTolerance = l / 10000.0
        except:
            obj.ApproxTolerance = 0.001

    def getPoints( self, obj):
        return(_utils.getShape(obj, "PointList", "Vertex")) 

    def execute(self, obj):
        debug("\n* Interpolate : execute *\n")
        pts = self.getPoints( obj)
        bs = Part.BSplineCurve()
        bs.interpolate(Points=pts, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Parameters=obj.Parameters, Tangents=obj.Tangents, TangentFlags=obj.TangentFlags)
        obj.Shape = bs.toShape()


    def onChanged(self, fp, prop):
        #print fp
        if not fp.PointObject:
            return
        if prop == "PointObject":
            debug("Approximate : PointObject changed\n")
            num = len(self.Points)
            diff = num - fp.LastIndex -1
            self.getPoints( fp)
            #fp.FirstIndex = 0
            fp.LastIndex = len(self.Points)-diff

        if prop == "Parametrization":
            debug("Approximate : Parametrization changed\n")
            props = ["ClampEnds","DegreeMin","DegreeMax","Continuity"]
            if fp.Parametrization == "Curvilinear":
                if hasattr(fp.PointObject,"Distance"):
                    for p in props:
                        fp.setEditorMode(p, 2)
                else:
                    fp.Parametrization == "ChordLength"
            else:
                for p in props:
                    fp.setEditorMode(p, 0)   

        if prop == "Method":
            debug("Approximate : Method changed\n")
            if fp.Method == "Parametrization":
                fp.setEditorMode("Parametrization", 0)
                fp.setEditorMode("LengthWeight", 2)
                fp.setEditorMode("CurvatureWeight", 2)
                fp.setEditorMode("TorsionWeight", 2)
            elif fp.Method == "Smoothing Algorithm":
                fp.setEditorMode("Parametrization", 2)
                fp.setEditorMode("LengthWeight", 0)
                fp.setEditorMode("CurvatureWeight", 0)
                fp.setEditorMode("TorsionWeight", 0)
                if fp.Continuity in ["C3","CN"]:
                    fp.Continuity = 'C2'
                    
        if prop == "Continuity":
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity == 'C1':
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
                elif fp.Continuity in ['G1','G2','C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
            debug("Approximate : Continuity changed to "+str(fp.Continuity))

        if prop == "DegreeMin":
            if fp.DegreeMin < 1:
                fp.DegreeMin = 1
            elif fp.DegreeMin > fp.DegreeMax:
                fp.DegreeMin = fp.DegreeMax
            debug("Approximate : DegreeMin changed to "+str(fp.DegreeMin))
        if prop == "DegreeMax":
            if fp.DegreeMax < fp.DegreeMin:
                fp.DegreeMax = fp.DegreeMin
            elif fp.DegreeMax > 14:
                fp.DegreeMax = 14
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity in ['G1','G2','C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
                elif fp.Continuity == "C1":
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
            debug("Approximate : DegreeMax changed to "+str(fp.DegreeMax))
        if prop == "ApproxTolerance":
            if fp.ApproxTolerance < 1e-6:
                fp.ApproxTolerance = 1e-6
            elif fp.ApproxTolerance > 1000.0:
                fp.ApproxTolerance = 1000.0
            debug("Approximate : ApproxTolerance changed to "+str(fp.ApproxTolerance))

        if prop == "FirstIndex":
            if fp.FirstIndex < 0:
                fp.FirstIndex = 0
            elif fp.FirstIndex > fp.LastIndex-1:
                fp.FirstIndex = fp.LastIndex-1
            debug("Approximate : FirstIndex changed to "+str(fp.FirstIndex))
        if prop == "LastIndex":
            if fp.LastIndex < fp.FirstIndex+1:
                fp.LastIndex = fp.FirstIndex+1
            elif fp.LastIndex > len(self.Points)-1:
                fp.LastIndex = len(self.Points)-1
            debug("Approximate : LastIndex changed to "+str(fp.LastIndex))

            
    def __getstate__(self):
        out = {"name": self.obj.Name,
               "Method": self.obj.Method}
        return out

    def __setstate__(self,state):
        self.obj = FreeCAD.ActiveDocument.getObject(state["name"])
        if not "Method" in self.obj.PropertiesList:
            self.obj.addProperty("App::PropertyEnumeration",  "Method",       "General",     "Approximation method").Method=["Parametrization","Smoothing Algorithm"]
        if not "TorsionWeight" in self.obj.PropertiesList:
            self.obj.addProperty("App::PropertyFloatConstraint",        "TorsionWeight",   "Parameters",       "Weight of curve torsion for smoothing algorithm")
        self.obj.Method = state["Method"]
        self.getPoints(self.obj)
        return None

class ViewProviderInterpolate:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

    #def claimChildren(self):
        #return [self.Object.PointObject]
        
    #def onDelete(self, feature, subelements):
        #try:
            #self.Object.PointObject.ViewObject.Visibility=True
        #except Exception as err:
            #App.Console.PrintError("Error in onDelete: " + err.message)
        #return(True)

class interpolate:
    def parseSel(self, selectionObject):
        verts = list()
        for obj in selectionObject:
            if obj.HasSubObjects:
                for n in obj.SubElementNames:
                    if 'Vertex' in n:
                        verts.append((obj.Object,[n]))
        if res:
            return(res)
        else:
            FreeCAD.Console.PrintMessage("\nPlease select an object that has at least 2 vertexes")
            return(None)

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        source = self.parseSel(s)
        if not source:
            return(False)
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Interpolation_Curve") #add object to document
        Interpolate(obj,source)
        ViewProviderInterpolate(obj.ViewObject)
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Interpolate', 'ToolTip': 'Interpolate points with a BSpline curve'}

FreeCADGui.addCommand('Interpolate', interpolate())



