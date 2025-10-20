# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Freehand BSpline"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Creates an freehand BSpline curve"
__usage__ = """*** Interpolation curve control keys :

    a - Select all / Deselect
    i - Insert point in selected segments
    t - Set / unset tangent (view direction)
    p - Align selected objects
    s - Snap points on shape / Unsnap
    l - Set/unset a linear interpolation
    x,y,z - Axis constraints during grab
    q - Apply changes and quit editing"""

import os
import FreeCAD
import FreeCADGui
import Part
from . import ICONPATH
from . import _utils
from . import profile_editor


TOOL_ICON = os.path.join(ICONPATH, 'editableSpline.svg')
# debug = _utils.debug
debug = _utils.doNothing


def check_pivy():
    try:
        profile_editor.MarkerOnShape([FreeCAD.Vector()])
        return True
    except Exception as exc:
        FreeCAD.Console.PrintWarning(str(exc) + "\nPivy interaction library failure\n")
        return False


def midpoint(e):
    p = e.FirstParameter + 0.5 * (e.LastParameter - e.FirstParameter)
    return e.valueAt(p)


class GordonProfileFP:
    """Creates an editable interpolation curve"""
    def __init__(self, obj, s, d, t):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSubList", "Support", "Profile", "Constraint shapes").Support = s
        obj.addProperty("App::PropertyFloatConstraint", "Parametrization", "Profile", "Parametrization factor")
        obj.addProperty("App::PropertyFloat", "Tolerance", "Profile", "Tolerance").Tolerance = 1e-7
        obj.addProperty("App::PropertyBool", "Periodic", "Profile", "Periodic curve").Periodic = False
        obj.addProperty("App::PropertyVectorList", "Data", "Profile", "Data list").Data = d
        obj.addProperty("App::PropertyVectorList", "Tangents", "Profile", "Tangents list")
        obj.addProperty("App::PropertyBoolList", "Flags", "Profile", "Tangent flags")
        obj.addProperty("App::PropertyIntegerList", "DataType", "Profile", "Types of interpolated points").DataType = t
        obj.addProperty("App::PropertyBoolList", "LinearSegments", "Profile", "Linear segment flags")
        obj.Parametrization = (1.0, 0.0, 1.0, 0.05)
        obj.Proxy = self

    def get_shapes(self, fp):
        if hasattr(fp, 'Support'):
            sl = list()
            for ob, names in fp.Support:
                for name in names:
                    if "Vertex" in name:
                        n = eval(name.lstrip("Vertex"))
                        if len(ob.Shape.Vertexes) >= n:
                            sl.append(ob.Shape.Vertexes[n - 1])
                    elif ("Point" in name):
                        sl.append(Part.Vertex(ob.Shape.Point))
                    elif ("Edge" in name):
                        n = eval(name.lstrip("Edge"))
                        if len(ob.Shape.Edges) >= n:
                            sl.append(ob.Shape.Edges[n - 1])
                    elif ("Face" in name):
                        n = eval(name.lstrip("Face"))
                        if len(ob.Shape.Faces) >= n:
                            sl.append(ob.Shape.Faces[n - 1])
            return sl

    def get_points(self, fp, stretch=True):
        touched = False
        shapes = self.get_shapes(fp)
        if not len(fp.Data) == len(fp.DataType):
            FreeCAD.Console.PrintError("Gordon Profile : Data and DataType mismatch\n")
            return(None)
        pts = list()
        shape_idx = 0
        for i in range(len(fp.Data)):
            if fp.DataType[i] == 0:  # Free point
                pts.append(fp.Data[i])
            elif (fp.DataType[i] == 1):
                if (shape_idx < len(shapes)):  # project on shape
                    d, p, i = Part.Vertex(fp.Data[i]).distToShape(shapes[shape_idx])
                    if d > fp.Tolerance:
                        touched = True
                    pts.append(p[0][1])  # shapes[shape_idx].valueAt(fp.Data[i].x))
                    shape_idx += 1
                else:
                    pts.append(fp.Data[i])
        if stretch and touched:
            params = [0]
            knots = [0]
            moves = [pts[0] - fp.Data[0]]
            lsum = 0
            mults = [2]
            for i in range(1, len(pts)):
                lsum += fp.Data[i - 1].distanceToPoint(fp.Data[i])
                params.append(lsum)
                if fp.DataType[i] == 1:
                    knots.append(lsum)
                    moves.append(pts[i] - fp.Data[i])
                    mults.insert(1, 1)
            mults[-1] = 2
            if len(moves) < 2:
                return(pts)
            # FreeCAD.Console.PrintMessage("%s\n%s\n%s\n"%(moves,mults,knots))
            curve = Part.BSplineCurve()
            curve.buildFromPolesMultsKnots(moves, mults, knots, False, 1)
            for i in range(1, len(pts)):
                if fp.DataType[i] == 0:
                    # FreeCAD.Console.PrintMessage("Stretch %s #%d: %s to %s\n"%(fp.Label,i,pts[i],curve.value(params[i])))
                    pts[i] += curve.value(params[i])
        if touched:
            return pts
        else:
            return False

    def execute(self, obj):
        try:
            o = FreeCADGui.ActiveDocument.getInEdit().Object
            if o == obj:
                return
        except AttributeError:
            pass
        except:
            FreeCAD.Console.PrintWarning("execute is disabled during editing\n")
        pts = self.get_points(obj)
        if pts:
            if len(pts) < 2:
                FreeCAD.Console.PrintError("{} : Not enough points\n".format(obj.Label))
                return False
            else:
                obj.Data = pts
        else:
            pts = obj.Data

        tans = [FreeCAD.Vector()] * len(pts)
        flags = [False] * len(pts)
        for i in range(len(obj.Tangents)):
            tans[i] = obj.Tangents[i]
        for i in range(len(obj.Flags)):
            flags[i] = obj.Flags[i]
        # if not (len(obj.LinearSegments) == len(pts)-1):
            # FreeCAD.Console.PrintError("%s : Points and LinearSegments mismatch\n"%obj.Label)
        if len(obj.LinearSegments) > 0:
            for i, b in enumerate(obj.LinearSegments):
                if b:
                    tans[i] = pts[i + 1] - pts[i]
                    tans[i + 1] = tans[i]
                    flags[i] = True
                    flags[i + 1] = True
        params = profile_editor.parameterization(pts, obj.Parametrization, obj.Periodic)
        
        curve = Part.BSplineCurve()
        if len(pts) == 2:
            curve.buildFromPoles(pts)
        elif obj.Periodic and pts[0].distanceToPoint(pts[-1]) < 1e-7:
            curve.interpolate(Points=pts[:-1], Parameters=params, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Tangents=tans[:-1], TangentFlags=flags[:-1])
        else:
            curve.interpolate(Points=pts, Parameters=params, PeriodicFlag=obj.Periodic, Tolerance=obj.Tolerance, Tangents=tans, TangentFlags=flags)
        obj.Shape = curve.toShape()

    def onChanged(self, fp, prop):
        if prop in ("Support", "Data", "DataType", "Periodic"):
            # FreeCAD.Console.PrintMessage("%s : %s changed\n"%(fp.Label,prop))
            if (len(fp.Data) == len(fp.DataType)) and (sum(fp.DataType) == len(fp.Support)):
                new_pts = self.get_points(fp, True)
                if new_pts:
                    fp.Data = new_pts
        if prop == "Parametrization":
            self.execute(fp)

    def onDocumentRestored(self, fp):
        fp.setEditorMode("Data", 2)
        fp.setEditorMode("DataType", 2)


class GordonProfileVP:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.select_state = True
        self.active = False

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object
        self.active = False
        self.select_state = vobj.Selectable
        self.ip = None

    def setEdit(self, vobj, mode=0):
        if mode == 0 and check_pivy():
            pl = self.Object.Placement
            if vobj.Selectable:
                self.select_state = True
                vobj.Selectable = False
            pts = list()
            sl = list()
            for ob, names in self.Object.Support:
                for name in names:
                    sl.append((ob, (name,)))
            shape_idx = 0
            for i in range(len(self.Object.Data)):
                tp = self.Object.Data[i]
                p = pl.multVec(tp)
                t = self.Object.DataType[i]
                if t == 0:
                    pts.append(profile_editor.MarkerOnShape([p]))
                elif t == 1:
                    pts.append(profile_editor.MarkerOnShape([p], sl[shape_idx]))
                    shape_idx += 1
            for i in range(len(pts)):  # p,t,f in zip(pts, self.Object.Tangents, self.Object.Flags):
                if i < min(len(self.Object.Flags), len(self.Object.Tangents)):
                    if self.Object.Flags[i]:
                        pts[i].tangent = self.Object.Tangents[i]
            self.ip = profile_editor.InterpoCurveEditor(pts, self.Object)
            self.ip.periodic = self.Object.Periodic
            self.ip.param_factor = self.Object.Parametrization
            for i in range(min(len(self.Object.LinearSegments), len(self.ip.lines))):
                self.ip.lines[i].tangent = self.Object.LinearSegments[i]
                self.ip.lines[i].updateLine()
            self.active = True
            return True
        return False

    def unsetEdit(self, vobj, mode=0):
        if isinstance(self.ip, profile_editor.InterpoCurveEditor) and check_pivy():
            pts = list()
            typ = list()
            tans = list()
            flags = list()
            # original_links = self.Object.Support
            new_links = list()
            for p in self.ip.points:
                if isinstance(p, profile_editor.MarkerOnShape):
                    pt = p.points[0]
                    pts.append(FreeCAD.Vector(pt[0], pt[1], pt[2]))
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
            self.Object.LinearSegments = [li.linear for li in self.ip.lines]
            self.Object.DataType = typ
            self.Object.Data = pts
            self.Object.Support = new_links
            vobj.Selectable = self.select_state
            self.ip.quit()
        self.ip = None
        self.active = False
        self.Object.Document.recompute()
        return True

    def doubleClicked(self, vobj):
        if not hasattr(self, 'active'):
            self.active = False
        if not self.active:
            self.active = True
            # self.setEdit(vobj)
            vobj.Document.setEdit(vobj)
        else:
            vobj.Document.resetEdit()
            self.active = False
        return True

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


class GordonProfileCommand:
    """Creates a editable interpolation curve"""

    def makeFeature(self, sub, pts, typ):
        fp = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Freehand BSpline")
        GordonProfileFP(fp, sub, pts, typ)
        GordonProfileVP(fp.ViewObject)
        FreeCAD.Console.PrintMessage(__usage__)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.SendMsgToActiveView("ViewFit")
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
        for obj in s:
            if obj.HasSubObjects:
                # FreeCAD.Console.PrintMessage("object has subobjects %s\n"%str(obj.SubElementNames))
                for n in obj.SubElementNames:
                    sub.append((obj.Object, [n]))
                for p in obj.PickedPoints:
                    pts.append(p)

        if len(pts) == 0:
            pts = [FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(5, 0, 0), FreeCAD.Vector(10, 0, 0)]
            typ = [0, 0, 0]
        elif len(pts) == 1:
            pts.append(pts[0] + FreeCAD.Vector(5, 0, 0))
            pts.append(pts[0] + FreeCAD.Vector(10, 0, 0))
            typ = [1, 0, 0]
        else:
            typ = [1] * len(pts)
        self.makeFeature(sub, pts, typ)

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(__doc__, "<br>".join(__usage__.splitlines()))}


FreeCADGui.addCommand('gordon_profile', GordonProfileCommand())
