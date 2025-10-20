# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Outline Curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Outline curve of a shape"""

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils
import approximate_extension

TOOL_ICON = _utils.iconsPath() + 'icon.svg'
#debug = _utils.debug
#debug = _utils.doNothing

props = """
App::PropertyBool
App::PropertyBoolList
App::PropertyFloat
App::PropertyFloatList
App::PropertyFloatConstraint
App::PropertyQuantity
App::PropertyQuantityConstraint
App::PropertyAngle
App::PropertyDistance
App::PropertyLength
App::PropertySpeed
App::PropertyAcceleration
App::PropertyForce
App::PropertyPressure
App::PropertyInteger
App::PropertyIntegerConstraint
App::PropertyPercent
App::PropertyEnumeration
App::PropertyIntegerList
App::PropertyIntegerSet
App::PropertyMap
App::PropertyString
App::PropertyUUID
App::PropertyFont
App::PropertyStringList
App::PropertyLink
App::PropertyLinkSub
App::PropertyLinkList
App::PropertyLinkSubList
App::PropertyMatrix
App::PropertyVector
App::PropertyVectorList
App::PropertyPlacement
App::PropertyPlacementLink
App::PropertyColor
App::PropertyColorList
App::PropertyMaterial
App::PropertyPath
App::PropertyFile
App::PropertyFileIncluded
App::PropertyPythonObject
Part::PropertyPartShape
Part::PropertyGeometryList
Part::PropertyShapeHistory
Part::PropertyFilletEdges
Sketcher::PropertyConstraintList
"""

class OutlineFP:
    """Creates a Outline curve"""
    def __init__(self, obj, s):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Source", "Outline", "Source object").Source = s
        obj.addProperty("App::PropertyVector", "Direction", "Outline", "Direction Vector").Direction = FreeCAD.Vector(0,0,1)
        obj.addProperty("App::PropertyInteger", "RadialSamples", "Outline", "Number of samples around object").RadialSamples = 360
        obj.Proxy = self

    def execute(self, obj):
        o = obj.Source
        base = o.Shape.BoundBox.Center
        dl = o.Shape.BoundBox.DiagonalLength
        cyl = Part.makeCylinder(dl, dl*2, base-obj.Direction*dl, obj.Direction).Face1

        uf,ul,vf,vl=cyl.ParameterRange
        pts = list()
        for i in range(obj.RadialSamples):
            u = uf + (float(i)/(obj.RadialSamples-1))*(ul-uf)
            e = cyl.Surface.uIso(u).toShape()
            #best = 1e50
            #good_pt = None
            d,pt,info = o.Shape.distToShape(e)
            if len(pt) > 1:
                debug("multi pt %s"%str(pt))
                #good_point = pt[0][0]
            for i,inf in enumerate(info):
                if inf[0] in (b"Face","Face"):
                    pts.append(pt[i][0])


        if hasattr(obj,"ExtensionProxy"):
            if obj.Active:
                obj.Shape = obj.ExtensionProxy.approximate(obj, pts)
                return()
        bs = Part.BSplineCurve()
        bs.approximate(pts)
        obj.Shape = bs.toShape()

    def onChanged(self, fp, prop):
        if hasattr(fp,"ExtensionProxy"):
            fp.ExtensionProxy.onChanged(fp, prop)
        #return(False)

class OutlineVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

class outline_cmd:
    """Creates a Outline curve"""
    def makeFeature(self,sel):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Outline Curve")
        OutlineFP(fp, sel)
        approximate_extension.ApproximateExtension(fp)
        fp.Active = False
        OutlineVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select something first !\n")
        else:
            self.makeFeature(sel[0])

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}

FreeCADGui.addCommand('outline', outline_cmd())
