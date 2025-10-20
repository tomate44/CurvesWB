# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Trim face'
__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Trim a face with a projected curve'

import os
import FreeCAD
import FreeCADGui
import Part
# from freecad.Curves import _utils
from freecad.Curves import ICONPATH

try:
    import BOPTools.SplitAPI
    splitAPI = BOPTools.SplitAPI
except ImportError:
    FreeCAD.Console.PrintError("Failed importing BOPTools. Fallback to Part API\n")
    splitAPI = Part.BOPTools.SplitAPI

TOOL_ICON = os.path.join(ICONPATH, 'trimFace.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class trimFace:
    def __init__(self, obj):
        ''' Add the properties '''
        debug("\ntrimFace init")
        obj.addProperty("App::PropertyLinkSub", "Face",
                        "TrimFace", "Input face")
        obj.addProperty("App::PropertyVector", "PickedPoint",
                        "TrimFace", "Picked point in parametric space of the face (u,v,0)")
        obj.addProperty("App::PropertyLinkSubList", "Tool",
                        "TrimFace", "Trimming curve")
        obj.addProperty("App::PropertyLink", "DirVector",
                        "TrimFace", "Trimming Vector")
        obj.addProperty("App::PropertyVector", "Direction",
                        "TrimFace", "Trimming direction")
        obj.Proxy = self

    def getFace(self, link):
        o = link[0]
        shapelist = link[1]
        for s in shapelist:
            if 'Face' in s:
                n = eval(s.lstrip('Face'))
                debug("Face {}".format(n))
                return(o.Shape.Faces[n - 1])
        return None

    def getEdges(self, sublinks):
        res = []
        for link in sublinks:
            o = link[0]
            shapelist = link[1]
            for s in shapelist:
                if 'Edge' in s:
                    n = eval(s.lstrip('Edge'))
                    debug("Edge {}".format(n))
                    res.append(o.Shape.Edges[n - 1])
        return res

    def getVector(self, obj):
        if hasattr(obj, "DirVector"):
            if obj.DirVector:
                v = FreeCAD.Vector(obj.DirVector.Direction)
                debug("choosing DirVector : {}".format(str(v)))
                if v.Length > 1e-6:
                    return v
        if hasattr(obj, "Direction"):
            if obj.Direction:
                v = FreeCAD.Vector(obj.Direction)
                debug("choosing Direction : {}".format(str(v)))
                if v.Length > 1e-6:
                    return v
        debug("choosing (0,0,-1)")
        return FreeCAD.Vector(0, 0, -1)

    def execute(self, obj):
        debug("* trimFace execute *")
        if not obj.Tool:
            debug("No tool")
            return
        if not obj.PickedPoint:
            debug("No PickedPoint")
            return
        if not obj.Face:
            debug("No Face")
            return
        if not (obj.DirVector or obj.Direction):
            debug("No Direction")
            return

        face = self.getFace(obj.Face)
        v = self.getVector(obj)
        v.normalize()
        debug("Vector : {}".format(str(v)))
        wires = [Part.Wire(el) for el in Part.sortEdges(self.getEdges(obj.Tool))]
        union = Part.Compound(wires + [face])
        d = 2 * union.BoundBox.DiagonalLength
        cuttool = []
        for w in wires:
            w.translate(v * d)
            cuttool.append(w.extrude( - v * d * 2))
        # Part.show(cuttool)

        bf = splitAPI.slice(face, cuttool, "Split", 1e-6)
        debug("shape has {} faces".format(len(bf.Faces)))

        u = obj.PickedPoint.x
        v = obj.PickedPoint.y
        for f in bf.Faces:
            if f.isPartOfDomain(u, v):
                obj.Shape = f
                return


class trimFaceVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def doubleClicked(self, vobj):
        if hasattr(self.Object, "Direction"):
            d = self.Object.Direction
            FreeCADGui.ActiveDocument.ActiveView.setViewDirection((d.x, d.y, d.z))
            return True

    def claimChildren(self):
        children = []
        if hasattr(self.Object, "DirVector"):
            if self.Object.DirVector:
                children.append(self.Object.DirVector)
        if hasattr(self.Object, "Face"):
            if self.Object.Face:
                children.append(self.Object.Face[0])
        if hasattr(self.Object, "Tool"):
            if self.Object.Tool:
                children.append(self.Object.Tool[0])
        return children

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


class trim:
    def findVector(self, selectionObject):
        res = selectionObject[:]
        i = 0
        for obj in selectionObject:
            if hasattr(obj.Object, "Direction") and hasattr(obj.Object, "Origin"):
                v = obj.Object
                res.pop(i)
                return (v, res)
            i += 1
        return None, selectionObject

    def findCurve(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj), Part.Edge):
                        # res.pop(i)
                        res.append((obj.Object, obj.SubElementNames[i]))
                    i += 1
        return res, selectionObject

    def findFaces(self, selectionObject):
        res = []
        for obj in selectionObject:
            if obj.HasSubObjects:
                i = 0
                for subobj in obj.SubObjects:
                    if issubclass(type(subobj), Part.Face):
                        f = (obj.Object, [obj.SubElementNames[i]])
                        p = obj.PickedPoints[i]
                        u, v = subobj.Surface.parameter(p)
                        res.append((f, FreeCAD.Vector(u, v, 0)))
                    i += 1
        return res

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        vector, selObj1 = self.findVector(s)
        trimmingCurve, selObj2 = self.findCurve(selObj1[::-1])
        faces = self.findFaces(selObj2)

        if trimmingCurve and faces:
            for f in faces:
                obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "TrimmedFace")
                trimFace(obj)
                trimFaceVP(obj.ViewObject)
                obj.Face = f[0]
                obj.Face[0].ViewObject.Visibility = False
                obj.PickedPoint = f[1]
                obj.Tool = trimmingCurve
                # obj.Tool[0].ViewObject.Visibility=False
                if vector:
                    obj.DirVector = vector
                    obj.DirVector.ViewObject.Visibility = False
                else:
                    obj.Direction = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('Trim', trim())



