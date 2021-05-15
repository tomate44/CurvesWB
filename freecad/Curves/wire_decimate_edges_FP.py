# -*- coding: utf-8 -*-

__title__ = "Simplify"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Reduce the number of edges of wires and faces"
__usage__ = """Select an object containing wires or faces in the 3D View and activate the tool.
Edges that are connected with an angle that is under a given angular threshold will be fused together
into an approximated C1 BSpline curve."""

import os
import FreeCAD
import FreeCADGui
import Part
from . import wire_tools
from . import face_tools
from . import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, "simplify_wire.svg")


class DecimateProxy:
    """Reduce the number of edges of wires and faces"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLinkSubList", "Source", "Decimate", "Source object")
        obj.addProperty("App::PropertyFloat", "Angle", "Settings", "Angular threshold").Angle = 30
        obj.addProperty("App::PropertyBool", "ForceC1", "Settings", "Force C1 continuity by approximation").ForceC1 = False
        obj.addProperty("App::PropertyFloat", "Tolerance", "Settings", "3D Tolerance of approximation").Tolerance = 1e-3
        obj.addProperty("App::PropertyInteger", "Samples", "Settings", "Number of edge samples for approximation").Samples = 20
        obj.Proxy = self

    def get_shapes(self, obj):
        edges = []
        wires = []
        faces = []
        for link in obj.Source:
            if link[1][0]:
                for sename in link[1]:
                    if "Edge" in sename:
                        edges.append(link[0].getSubObject(sename))
                    elif "Face" in sename:
                        faces.append(link[0].getSubObject(sename))
            else:
                if link[0].Shape.Faces:
                    faces.extend(link[0].Shape.Faces)
                elif link[0].Shape.Wires:
                    wires.extend(link[0].Shape.Wires)
                elif link[0].Shape.Edges:
                    edges.extend(link[0].Shape.Edges)
        for el in Part.sortEdges(edges):
            wires.append(Part.Wire(el))
        return wires, faces

    def onChanged(self, fp, prop):
        if 'Restore' in fp.State:
            return
        if prop == "Angle":
            if fp.Angle < 0:
                fp.Angle = 0
            elif fp.Angle > 180:
                fp.Angle = 180
        if prop == "Samples":
            if fp.Samples < 2:
                fp.Samples = 2
            elif fp.Samples > 1000:
                fp.Samples = 1000
        if prop == "Tolerance":
            if fp.Tolerance < 1e-7:
                fp.Tolerance = 1e-7

    def execute(self, fp):
        wires, faces = self.get_shapes(fp)
        print("{} wires, {} faces".format(len(wires), len(faces)))
        new_wires = []
        new_faces = []
        for w in wires:
            new_wires.append(wire_tools.simplify_wire(w, fp.Angle, fp.Tolerance, fp.Samples, fp.ForceC1))
        for f in faces:
            fwires = []
            for w in f.Wires:
                fwires.append(wire_tools.simplify_wire(w, fp.Angle, fp.Tolerance, fp.Samples, fp.ForceC1))
            new_faces.extend(face_tools.build_faces(fwires, f))
        fp.Shape = Part.Compound(new_wires + new_faces)


class DecimateViewProxy:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

    def claimChildren(self):
        children = []
        for o in self.Object.Source:
            if len(o[1][0]) == 0:  # No sub-objects
                children.append(o[0])
        return children


class DecimateEdgesCommand:
    """Reduce the number of edges of wires and faces"""
    def makeDecimateFeature(self, source):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Simplify")
        DecimateProxy(fp)
        DecimateViewProxy(fp.ViewObject)
        fp.Source = source
        fp.Tolerance = source[0].Shape.BoundBox.DiagonalLength * 1e-4
        # Hide Tree-View selection
        if len(source[1]) == 0:  # No sub-objects
                source[0].ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("{} :\n{}\n".format(__title__, __usage__))
        for selobj in sel:
            self.makeDecimateFeature((selobj.Object, selobj.SubElementNames))

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}\n\n{}\n\n{}".format(__title__, __doc__, __usage__)}


FreeCADGui.addCommand('Curves_decimate_edges', DecimateEdgesCommand())
