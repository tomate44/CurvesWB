# -*- coding: utf-8 -*-

__title__ = "Parametric Gordon surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates a surface that skins a network of curves."

import sys
if sys.version_info.major >= 3:
    from importlib import reload

import FreeCAD
import FreeCADGui
import Part
import _utils

TOOL_ICON = _utils.iconsPath() + '/gordon.svg'
debug = _utils.debug
debug = _utils.doNothing

class gordon:
    """Creates a surface that skins a network of curves"""
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkList", "Sources", "Gordon", "Curve network")
        obj.addProperty("App::PropertyFloat", "Tol3D", "Gordon", "3D tolerance").Tol3D = 1e-5
        obj.addProperty("App::PropertyFloat", "Tol2D", "Gordon", "Parametric tolerance").Tol2D = 1e-8
        obj.Proxy = self

    def execute(self, obj):
        if len(obj.Sources) == 0:
            return()
        elif len(obj.Sources) == 2:
            guides = obj.Sources[0].Shape.Edges
            profiles = obj.Sources[1].Shape.Edges
        else:
            edges = list()
            for o in obj.Sources:
                edges += o.Shape.Edges
            profiles = list()
            e0 = edges[0]
            guides = [e0]
            for e in edges[1:]:
                d,pts,info = e0.distToShape(e)
                if d < obj.Tol3D:
                    profiles.append(e)
                else:
                    guides.append(e)
        
        import gordon
        reload(gordon)
        guide_curves = [e.Curve.toBSpline() for e in guides]
        profile_curves = [e.Curve.toBSpline() for e in profiles]

        # create the gordon surface
        gordon = gordon.InterpolateCurveNetwork(profile_curves, guide_curves, obj.Tol3D, obj.Tol2D)

        # display curves and resulting surface
        obj.Shape = gordon.surface().toShape()

class gordonVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return(None)

class gordonCommand:
    """Creates a surface that skins a network of curves"""
    def makeGordonFeature(self,source):
        gordonObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Gordon")
        gordon(gordonObj)
        gordonVP(gordonObj.ViewObject)
        gordonObj.Sources = source
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if sel == []:
            FreeCAD.Console.PrintError("Select a curve network !\n")
        else:
            self.makeGordonFeature(sel)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            f = FreeCADGui.Selection.Filter("SELECT Part::Feature COUNT 1..100")
            return f.match()
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'Gordon surface', 'ToolTip': 'Creates a surface that skins a network of curves'}

FreeCADGui.addCommand('gordon', gordonCommand())
