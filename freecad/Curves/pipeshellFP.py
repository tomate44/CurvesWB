# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = 'Pipeshell'
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = 'Creates a PipeShell sweep object'

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'pipeshell.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class pipeShell:
    "PipeShell featurePython object"

    def __init__(self, obj):
        ''' Add the properties '''
        obj.addProperty("App::PropertyLinkSubList", "Spine", "Main", "Sweep path")
        obj.addProperty("App::PropertyLinkList", "Profiles", "Main", "Profiles that are swept along spine")
        obj.addProperty("App::PropertyLink", "Support", "Mode", "Shape of the ShapeSupport mode")
        obj.addProperty("App::PropertyLink", "Auxiliary", "Mode", "Auxiliary spine")
        obj.addProperty("App::PropertyEnumeration", "Mode", "Main", "PipeShell mode").Mode = ["Frenet", "DiscreteTrihedron", "FixedTrihedron", "Binormal", "ShapeSupport", "AuxiliarySpine"]
        obj.addProperty("App::PropertyEnumeration", "Output", "Main", "Output shape").Output = ["Sections", "Lofted sections", "Surface"]
        obj.addProperty("App::PropertyBool", "Solid", "Settings", "Make solid object").Solid = False
        obj.addProperty("App::PropertyInteger", "MaxDegree", "Settings", "Maximum degree of the generated surface").MaxDegree = 5
        obj.addProperty("App::PropertyInteger", "MaxSegments", "Settings", "Maximum number of segments of the generated surface").MaxSegments = 999
        obj.addProperty("App::PropertyInteger", "Samples", "Settings", "Number of samples for preview").Samples = 100
        obj.addProperty("App::PropertyFloat", "Tol3d", "Settings", "Tolerance 3D").Tol3d = 1.0e-4
        obj.addProperty("App::PropertyFloat", "TolBound", "Settings", "Tolerance boundary").TolBound = 1.0e-4
        obj.addProperty("App::PropertyFloat", "TolAng", "Settings", "Tolerance angular").TolAng = 1.0e-2
        obj.addProperty("App::PropertyVector", "Direction", "Mode", "Direction of the Binormal and FixedTrihedron modes")
        obj.addProperty("App::PropertyVector", "Location", "Mode", "Location of the FixedTrihedron mode")
        obj.addProperty("App::PropertyBool", "Corrected", "Mode", "Corrected Frenet").Corrected = False
        obj.addProperty("App::PropertyBool", "EquiCurvi", "Mode", "Curvilinear equivalence").EquiCurvi = False
        obj.addProperty("App::PropertyEnumeration", "Contact", "Mode", "Type of contact to auxiliary spine").Contact = ["NoContact", "Contact", "ContactOnBorder"]
        obj.Mode = "DiscreteTrihedron"
        obj.Contact = "NoContact"
        obj.Output = "Sections"
        obj.Direction = FreeCAD.Vector(0, 0, 1)
        obj.Location = FreeCAD.Vector(0, 0, 0)
        obj.Proxy = self

    def getprop(self, obj, prop):
        if hasattr(obj, prop):
            return obj.getPropertyByName(prop)
        else:
            FreeCAD.Console.PrintError("\n%s object has no property %s\n" % (obj.Label, prop))
            return None

    def getWires(self, obj, prop):
        res = []
        content = self.getprop(obj, prop)
        if isinstance(content, (list, tuple)):
            for li in content:
                res.append(li.Shape.Wires[0])
            return res
        else:
            if content.Shape.Wires:
                return content.Shape.Wires[0]
            elif content.Shape.Edges:
                return Part.Wire([content.Shape.Edges[0]])

    def getVertex(self, obj, prop):
        res = None
        content = self.getprop(obj, prop)
        if not content:
            return res
        o = content[0]
        for ss in content[1]:
            n = eval(ss.lstrip('Vertex'))
            res = o.Shape.Vertexes[n - 1]
        return res

    def onChanged(self, fp, prop):
        debug("%s changed" % prop)
        if prop == "Mode":
            if fp.Mode == "Frenet":
                fp.setEditorMode("Corrected", 0)
                fp.setEditorMode("Location", 2)
                fp.setEditorMode("Direction", 2)
                fp.setEditorMode("Auxiliary", 2)
                fp.setEditorMode("Support", 2)
                fp.setEditorMode("EquiCurvi", 2)
                fp.setEditorMode("Contact", 2)
            elif fp.Mode == "DiscreteTrihedron":
                fp.setEditorMode("Corrected", 2)
                fp.setEditorMode("Location", 2)
                fp.setEditorMode("Direction", 2)
                fp.setEditorMode("Auxiliary", 2)
                fp.setEditorMode("Support", 2)
                fp.setEditorMode("EquiCurvi", 2)
                fp.setEditorMode("Contact", 2)
            elif fp.Mode == "FixedTrihedron":
                fp.setEditorMode("Corrected", 2)
                fp.setEditorMode("Location", 0)
                fp.setEditorMode("Direction", 0)
                fp.setEditorMode("Auxiliary", 2)
                fp.setEditorMode("Support", 2)
                fp.setEditorMode("EquiCurvi", 2)
                fp.setEditorMode("Contact", 2)
            elif fp.Mode == "Binormal":
                fp.setEditorMode("Corrected", 2)
                fp.setEditorMode("Location", 2)
                fp.setEditorMode("Direction", 0)
                fp.setEditorMode("Auxiliary", 2)
                fp.setEditorMode("Support", 2)
                fp.setEditorMode("EquiCurvi", 2)
                fp.setEditorMode("Contact", 2)
            elif fp.Mode == "ShapeSupport":
                fp.setEditorMode("Corrected", 2)
                fp.setEditorMode("Location", 2)
                fp.setEditorMode("Direction", 2)
                fp.setEditorMode("Auxiliary", 2)
                fp.setEditorMode("Support", 0)
                fp.setEditorMode("EquiCurvi", 2)
                fp.setEditorMode("Contact", 2)
            elif fp.Mode == "AuxiliarySpine":
                fp.setEditorMode("Corrected", 2)
                fp.setEditorMode("Location", 2)
                fp.setEditorMode("Direction", 2)
                fp.setEditorMode("Auxiliary", 0)
                fp.setEditorMode("Support", 2)
                fp.setEditorMode("EquiCurvi", 0)
                fp.setEditorMode("Contact", 0)
        if prop == "MaxDegree":
            if fp.MaxDegree < 3:
                fp.MaxDegree = 3
            elif fp.MaxDegree > 14:
                fp.MaxDegree = 14
        if prop == "MaxSegments":
            if fp.MaxSegments < 1:
                fp.MaxSegments = 1
            elif fp.MaxSegments > 999:
                fp.MaxSegments = 999
        if prop == "Samples":
            if fp.Samples < 3:
                fp.Samples = 3
            elif fp.Samples > 999:
                fp.Samples = 999
        if prop == "Tol3d":
            if fp.Tol3d < 1e-7:
                fp.Tol3d = 1e-7
            elif fp.Tol3d > 1000:
                fp.Tol3d = 1000
        if prop == "TolBound":
            if fp.TolBound < 1e-7:
                fp.TolBound = 1e-7
            elif fp.TolBound > 1000:
                fp.TolBound = 1000
        if prop == "TolAng":
            if fp.TolAng < 1e-7:
                fp.TolAng = 1e-7
            elif fp.TolAng > 1000:
                fp.TolAng = 1000
        if prop == "Contact":
            if fp.Contact == "ContactOnBorder":
                FreeCAD.Console.PrintError("\nSorry, ContactOnBorder option is currently broken in OCCT.\n")
                fp.Contact = "Contact"

    def add(self, ps, p):
        contact = self.getprop(p, "Contact")
        correction = self.getprop(p, "Correction")
        loc = self.getVertex(p, "Location")
        for shape in p.Shape.Wires:
            if loc:
                debug("Adding Profile %s at location %s" % (p.Label, loc.Point))
                ps.add(shape, loc, contact, correction)
            else:
                debug("Adding Profile %s" % p.Label)
                ps.add(shape, contact, correction)

    def execute(self, obj):
        debug("\n\nExecuting PipeShell\n")
        path = None
        profs = []
        edges = _utils.getShape(obj, "Spine", "Edge")
        path = Part.Wire(Part.__sortEdges__(edges))
        if path.isValid():
            debug("Valid spine : %s" % path)
        if hasattr(obj, "Profiles"):
            profs = obj.Profiles
        if not (path and profs):
            return None
        debug("Creating PipeShell")
        # create the pipeShell object
        ps = Part.BRepOffsetAPI.MakePipeShell(path)
        ps.setMaxDegree(self.getprop(obj, "MaxDegree") or 3)
        ps.setMaxSegments(self.getprop(obj, "MaxSegments") or 32)
        t3 = self.getprop(obj, "Tol3d") or 1.0e-4
        tb = self.getprop(obj, "TolBound") or 1.0e-4
        ta = self.getprop(obj, "TolAng") or 1.0e-2
        ps.setTolerance(t3, tb, ta)

        mode = self.getprop(obj, "Mode")  # or "DiscreteTrihedron"
        if mode in ["Binormal", "FixedTrihedron"]:
            direction = self.getprop(obj, "Direction")
            if not direction:
                direction = FreeCAD.Vector(0, 0, 1)
                obj.Direction = direction
                FreeCAD.Console.PrintError("\nWrong direction, defaulting to +Z\n")
            elif direction.Length < 1e-7:
                direction = FreeCAD.Vector(0, 0, 1)
                obj.Direction = direction
                FreeCAD.Console.PrintError("\nDirection has null length, defaulting to +Z\n")
            if mode == "Binormal":
                debug("Binormal mode (%r)" % direction)
                ps.setBiNormalMode(direction)
            elif mode == "FixedTrihedron":
                loc = self.getprop(obj, "Location") or FreeCAD.Vector(0, 0, 0)
                debug("FixedTrihedron mode (%r %r)" % (loc, direction))
                ps.setTrihedronMode(loc, direction)
        elif mode == "Frenet":
            fre = self.getprop(obj, "Corrected")
            debug("Frenet mode (%r)" % fre)
            ps.setFrenetMode(fre)
        elif mode == "AuxiliarySpine":
            aux = self.getprop(obj, "Auxiliary")
            w = None
            if aux:
                if aux.Shape.Wires:
                    w = aux.Shape.Wires[0]
                elif aux.Shape.Edges:
                    w = Part.Wire(Part.__sortEdges__(aux.Shape.Edges))
            if w:
                curv = self.getprop(obj, "EquiCurvi") or False
                cont = self.getprop(obj, "Contact") or "NoContact"
                n = self.getCode(cont)
                debug("AuxiliarySpine mode (%r %s)" % (curv, cont))
                ps.setAuxiliarySpine(w, curv, n)
            else:
                FreeCAD.Console.PrintError("\nPlease set a valid Auxiliary Spine Object\n")
        elif mode == "ShapeSupport":
            sup = self.getprop(obj, "Support")
            sh = None
            if sup:
                sh = sup.Shape
            if sh:
                debug("ShapeSupport mode")
                ps.setSpineSupport(sh)
            else:
                FreeCAD.Console.PrintError("\nPlease set a valid Spine support Object\n")

        for p in profs:
            self.add(ps, p)

        if ps.isReady():
            output = self.getprop(obj, "Output")
            solid = self.getprop(obj, "Solid") or False
            if (output == "Surface") or (not hasattr(ps, 'simulate')):
                ps.build()
                if solid:
                    ps.makeSolid()
                obj.Shape = ps.shape()
            else:
                shapes = ps.simulate(self.getprop(obj, "Samples") or 100)
                if output == "Lofted sections":
                    obj.Shape = Part.makeLoft(shapes, solid, False, False, self.getprop(obj, "MaxDegree"))
                else:
                    rails = self.getRails(shapes)
                    c = Part.Compound(shapes + rails)
                    obj.Shape = c
        else:
            FreeCAD.Console.PrintError("\nFailed to create shape\n")

    def getCode(self, cont):
        if cont == "Contact":
            return 1
        elif cont == "ContactOnBorder":
            return 2
        else:
            return 0

    def getRails(self, shapes):
        nbvert = len(shapes[0].Vertexes)
        edges = []
        for i in range(nbvert):
            pts = []
            for s in shapes:
                pts.append(s.Vertexes[i].Point)
            try:
                bs = Part.BSplineCurve()
                bs.interpolate(pts)
                edges.append(bs.toShape())
                debug("Rail %d : BSpline curve" % i)
            except Part.OCCError:
                po = Part.makePolygon(pts)
                edges.append(po)
                debug("Rail %d : Polygon" % i)
        return edges


class pipeShellVP:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def setEdit(self, vobj, mode):
        return False

    def unsetEdit(self, vobj, mode):
        return

    if FreeCAD.Version()[0] == '0' and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return None

        def loads(self, state):
            return None

    else:
        def __getstate__(self):
            return None

        def __setstate__(self, state):
            return None

    def claimChildren(self):
        return (self.Object.Profiles + [self.Object.Spine])

    def onDelete(self, feature, subelements):  # subelements is a tuple of strings
        return True


class pipeShellCommand:
    "creates a PipeShell feature python object"

    def makePipeShellFeature(self, path, profs):
        if path and profs:
            psfp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "PipeShell")
            pipeShell(psfp)
            psfp.Spine = path
            psfp.Profiles = profs
            pipeShellVP(psfp.ViewObject)
            # psfp.ViewObject.LineWidth = 2.0
            # psfp.ViewObject.LineColor = (0.5,0.8,0.3)
            psfp.Mode = "DiscreteTrihedron"
            FreeCAD.ActiveDocument.recompute()

    def Activated(self):
        path = list()
        profs = list()
        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.HasSubObjects:
                for sub in selobj.SubElementNames:
                    FreeCAD.Console.PrintMessage(sub + "\n")
                    if sub[0:4] == 'Edge':
                        path.append((selobj.Object, (sub, )))
            elif hasattr(selobj.Object, 'Proxy'):
                if selobj.Object.Proxy.__module__ == 'freecad.Curves.pipeshellProfileFP':
                    profs.append(selobj.Object)
        FreeCAD.Console.PrintMessage(str(path) + "\n")
        FreeCAD.Console.PrintMessage(str(profs) + "\n")
        if path and profs:
            # path.ViewObject.LineColor = (1.0,0.3,0.0)
            self.makePipeShellFeature(path, profs)
        else:
            FreeCAD.Console.PrintError("\nYou must select:\n- in the 3D view, the edges that build the sweep path\n- in the Tree view, one or more 'pipeshellProfile' objects\n")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


FreeCADGui.addCommand('pipeshell', pipeShellCommand())
