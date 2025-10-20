# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Reflect Lines"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates the reflect lines on a shape, according to a view direction"
__usage__ = """Select an object and activate tool.
This will create reflect lines according to the current view direction.
If selected object is a ReflectLines object, the view direction will be updated to the current camera direction.
If property OnShape is True, the lines will be ON the input shape (ViewPos and UpDir properties won't be used).
Otherwise, lines will be on the XY plane.
If view property TrackCam is True, the view direction will keep updating upon camera movements.
"""

import os
import FreeCAD
import FreeCADGui
import Part
from pivy import coin

from freecad.Curves import nurbs_tools
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'reflectLines.svg')


class ReflectLinesFP:
    """Creates the reflect lines on a shape, according to a view direction"""
    def __init__(self, obj, src):
        """Add the properties"""
        obj.addProperty("App::PropertyLink", "Source",
                        "ReflectLines", "Source object")
        obj.addProperty("App::PropertyLinkSubList", "IndivFaces",
                        "ReflectLines", "Individual faces")
        obj.addProperty("App::PropertyVector", "ViewPos",
                        "ReflectLines", "View position")
        obj.addProperty("App::PropertyVector", "ViewDir",
                        "ReflectLines", "View direction")
        obj.addProperty("App::PropertyVector", "UpDir",
                        "ReflectLines", "Up direction")
        obj.addProperty("App::PropertyBool", "RemoveDuplicates",
                        "CleaningOptions", "Remove duplicate edges").RemoveDuplicates = False
        obj.addProperty("App::PropertyInteger", "Samples",
                        "CleaningOptions", "Number of edge samples").Samples = 10
        obj.addProperty("App::PropertyQuantity", "CleaningTolerance",
                        "CleaningOptions", "CleaningTolerance for duplicate detection").CleaningTolerance = 1e-3
        obj.addProperty("App::PropertyBool", "IsoLine",
                        "EdgeType", "Isoparametric lines").IsoLine = True
        obj.addProperty("App::PropertyBool", "OutLine",
                        "EdgeType", "Outline silhouette lines").OutLine = True
        obj.addProperty("App::PropertyBool", "Rg1Line",
                        "EdgeType", "smooth edge of G1-continuity between two surfaces").Rg1Line = True
        obj.addProperty("App::PropertyBool", "RgNLine",
                        "EdgeType", "sewn edge of CN-continuity on one surface").RgNLine = True
        obj.addProperty("App::PropertyBool", "Sharp",
                        "EdgeType", "sharp edge (of C0-continuity)").Sharp = True
        obj.addProperty("App::PropertyBool", "Visible",
                        "ReflectLines", "Generate the visible lines, or the hidden lines").Visible = True
        obj.addProperty("App::PropertyBool", "OnShape",
                        "ReflectLines", "Output on-shape 3D lines").OnShape = True
        # obj.Samples = [10,3,999,1]
        obj.ViewPos = FreeCAD.Vector(0, 0, 0)
        obj.ViewDir = FreeCAD.Vector(0, 0, 1)
        obj.UpDir = FreeCAD.Vector(0, 1, 0)
        obj.setEditorMode("Samples", 2)
        obj.setEditorMode("CleaningTolerance", 2)
        if isinstance(src, (list, tuple)):
            obj.IndivFaces = src
        else:
            obj.Source = src
        obj.Proxy = self

    def execute(self, obj):
        sh = None
        rl = False
        plm = obj.Placement
        if len(obj.IndivFaces) > 0:
            faces = _utils.getShape(obj, "IndivFaces", "Face")
            sh = Part.Compound(faces)
        elif hasattr(obj.Source, "Shape"):
            sh = obj.Source.Shape
        try:
            shapes = []
            for prop in ["IsoLine", "OutLine", "Rg1Line", "RgNLine", "Sharp"]:
                if getattr(obj, prop):
                    rl = sh.reflectLines(ViewDir=obj.ViewDir, ViewPos=obj.ViewPos, UpDir=obj.UpDir, EdgeType=prop, Visible=obj.Visible, OnShape=obj.OnShape)
                    shapes.append(rl)
            rl = Part.Compound(shapes)
        except AttributeError:
            pass
        if rl and obj.RemoveDuplicates:
            edges = rl.Edges
            rl = Part.Compound(nurbs_tools.remove_subsegments(edges, num=obj.Samples, tol=obj.CleaningTolerance))
        if rl:
            obj.Shape = rl
            obj.Placement = plm

    def onChanged(self, obj, prop):
        if 'Restore' in obj.State:
            return
        if prop == "RemoveDuplicates":
            if obj.RemoveDuplicates:
                obj.setEditorMode("Samples", 0)
                obj.setEditorMode("CleaningTolerance", 0)
            else:
                obj.setEditorMode("Samples", 2)
                obj.setEditorMode("CleaningTolerance", 2)
        if prop == "OnShape":
            if obj.OnShape:
                obj.setEditorMode("ViewPos", 2)
                obj.setEditorMode("UpDir", 2)
            else:
                obj.setEditorMode("ViewPos", 0)
                obj.setEditorMode("UpDir", 0)
        if prop in ("Source", "ViewPos", "ViewDir", "UpDir", "visible", "OnShape",
                    "IsoLine", "OutLine", "Rg1Line", "RgNLine", "Sharp"):
            self.execute(obj)


class ReflectLinesVP:
    def __init__(self, vobj):
        vobj.addProperty("App::PropertyBool", "TrackCamera",
                        "AutoView", "Track camera movements").TrackCamera = False
        vobj.Proxy = self

    def onChanged(self, vobj, prop):
        if prop == 'TrackCamera':
            if vobj.TrackCamera:
                cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
                self.sensor.attach(cam)
            else:
                self.sensor.detach()

    def getIcon(self):
        return(TOOL_ICON)

    def attach(self, vobj):
        self.Object = vobj.Object
        self.sensor = coin.SoNodeSensor(self.cameramove, None)

    def cameramove(self, *args):
        self.Object.ViewDir = FreeCADGui.ActiveDocument.ActiveView.getCameraOrientation().multVec(FreeCAD.Vector(0,0,1))

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


class ReflectLinesCommand:
    """Creates the reflect lines on a shape, according to a view direction"""
    def makeFeature(self, s):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "ReflectLines")
        ReflectLinesFP(fp, s)
        ReflectLinesVP(fp.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        return fp

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select an object first !\n")
        else:
            rot = FreeCADGui.ActiveDocument.ActiveView.getCameraOrientation()
            vdir = FreeCAD.Vector(0, 0, 1)
            vdir = rot.multVec(vdir)
            udir = FreeCAD.Vector(0, 1, 0)
            udir = rot.multVec(udir)
            pos = FreeCADGui.ActiveDocument.ActiveView.getCameraNode().position.getValue().getValue()
            pos = FreeCAD.Vector(*pos)
            facelist = []
            for so in sel:
                o = so.Object
                if so.HasSubObjects:
                    facelist.append((o, so.SubElementNames))
                elif hasattr(o, "Proxy") and isinstance(o.Proxy, ReflectLinesFP):
                    o.ViewPos = pos
                    o.ViewDir = vdir
                    o.UpDir = udir
                else:
                    fp = self.makeFeature(o)
                    fp.ViewPos = pos
                    fp.ViewDir = vdir
                    fp.UpDir = udir
            if facelist:
                fp = self.makeFeature(facelist)
                fp.ViewPos = pos
                fp.ViewDir = vdir
                fp.UpDir = udir

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('ReflectLines', ReflectLinesCommand())
