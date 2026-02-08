# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "GeomInfo"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Display geometry information about selected shape"
__usage__ = """While active, this tool displays information about the geometry of an edge or face.
It displays poles, knots and weights of Bezier and BSpline curves and surfaces in the 3D View."""


import os
import re
import FreeCAD
import FreeCADGui
import Part
from . import _utils
from . import ICONPATH
from pivy import coin
from . import CoinNodes as coinNodes
from . import TOL3D
from freecad.Curves.lib.trimmed_surface import TrimmedSurface

TOOL_ICON = os.path.join(ICONPATH, 'info.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


# String formatting

def extract_name(obj):
    "Return the name of a Shape or Geometry object"
    t = str(obj)
    if (t[0] == "<") and (t[-1] == ">"):
        t = t[1:-1]
    return t.split()[0]


def format_weights(weights):
    "Return a list of formatted strings from BSpline weights"
    weightStr = []
    for w in weights:
        if abs(w - 1.0) < 0.001:
            weightStr.append("")
        elif w.is_integer():
            weightStr.append(f" {int(w)}")
        else:
            weightStr.append(f" {w:.2f}")
    return weightStr


def numbers_to_str(arr, num=20):
    """
    Return a formatted string from a number list
    If the array has more than 'num' items, string is truncated
    """
    strArr = ""
    if len(arr) > num:
        lim = num // 2
        return numbers_to_str(arr[0:lim]) + " ... " + numbers_to_str(arr[-lim:])
    for w in arr:
        if isinstance(w, float):
            strArr += f"{w:.2f}, "
        else:
            strArr += f"{w}, "
    return strArr[:-2]


def to1D(arr):
    "Return a list from a 2D array"
    array = []
    for row in arr:
        array.extend(row)
    return array


def paramList(n, fp, lp):
    "Return a list of n parameters in [fp, lp]"
    rang = lp - fp
    params = []
    if n == 1:
        params = [fp + rang / 2.0]
    elif n == 2:
        params = [fp, lp]
    elif n > 2:
        for i in range(n):
            params.append(fp + 1.0 * i * rang / (n - 1))
    return params


def edge_node(edge, color=(0.0, 0.0, 0.0), width=1, pattern=0xffff):
    "return a coin node of the edge, with specified color, width and pattern"
    full_node = _utils.rootNode(edge, 1, 0.05, 0.05)
    node = full_node.getChild(0)
    mat = node.getChild(0)
    mat.diffuseColor.setValues(0, 1, [color])
    style = node.getChild(1)
    style.lineWidth = width
    style.linePattern = pattern
    return node


def bsplinecurveNode(cur):
    bspline = False
    rational = False
    try:
        poles = cur.getPoles()
        weights = cur.getWeights()
    except AttributeError:
        return False
    try:
        rational = cur.isRational()
    except AttributeError:
        pass
    try:
        knots = cur.getKnots()
        mults = cur.getMultiplicities()
        bspline = True
    except AttributeError:
        bspline = False

    # *** Set poles ***
    polesnode = coinNodes.coordinate3Node(poles)

    # *** Set weights ***
    weightStr = format_weights(weights)

    polySep = coinNodes.polygonNode((0.5, 0.5, 0.5), 1)
    polySep.vertices = poles

    # *** Set markers ***
    markerSep = coinNodes.markerSetNode((1, 0, 0), coin.SoMarkerSet.DIAMOND_FILLED_9_9)
    markerSep.color = [(1, 0, 0)] + [(0.5, 0.0, 0.5)] * (len(poles) - 1)

    if rational:
        # *** Set weight text ***
        weightSep = coinNodes.multiTextNode((1, 0, 0),
                                            "osiFont,FreeSans,sans",
                                            16,
                                            0)
        weightSep.data = (poles, weightStr)

    if bspline:

        # *** Set knots ***
        knotPoints = []
        for k in knots:
            p = cur.value(k)
            knotPoints.append((p.x, p.y, p.z))
        knotsnode = coinNodes.coordinate3Node(knotPoints)
        # *** Set texts ***
        multStr = []
        for m in mults:
            multStr.append("\n%d" % m)

        knotMarkerSep = coinNodes.markerSetNode((0, 0, 1), coin.SoMarkerSet.CIRCLE_FILLED_5_5)
        knotMarkerSep.color = [(0, 0, 1)] * len(knotPoints)

        # *** Set mult text ***
        multSep = coinNodes.multiTextNode((0, 0, 1),
                                          "osiFont,FreeSans,sans",
                                          16,
                                          1)
        multSep.data = (knotPoints, multStr)

    vizSep = coin.SoSeparator()
    vizSep.addChild(polesnode)
    vizSep.addChild(polySep)
    vizSep.addChild(markerSep)
    if rational:
        vizSep.addChild(weightSep)
    if bspline:
        vizSep.addChild(knotsnode)
        vizSep.addChild(knotMarkerSep)
        vizSep.addChild(multSep)
    return vizSep


def bsplinesurfNode(surf):
    bspline = False
    rational = False
    try:
        poles = surf.getPoles()
        weights = surf.getWeights()
        nbU = int(surf.NbUPoles)
        nbV = int(surf.NbVPoles)
    except AttributeError:
        return False
    try:
        rational = surf.isURational() or surf.isVRational()
    except AttributeError:
        pass
    try:
        uknots = surf.getUKnots()
        vknots = surf.getVKnots()
        bspline = True
    except AttributeError:
        bspline = False

    # *** Set poles ***
    flatPoles = to1D(poles)
    polesnode = coinNodes.coordinate3Node(flatPoles)

    # *** Set weights ***
    flatW = to1D(weights)
    weightStr = format_weights(flatW)

    polyRowSep = coinNodes.rowNode((0.5, 0, 0), 1)
    polyRowSep.vertices = (nbU, nbV)
    polyRowSep.color = [(0.5, 0.0, 0.0)] * len(flatPoles)
    polyColSep = coinNodes.colNode((0, 0, 0.5), 1)
    polyColSep.vertices = (nbU, nbV)
    polyColSep.color = [(0.0, 0.0, 0.5)] * len(flatPoles)

    # *** Set markers ***
    markerSep = coinNodes.markerSetNode((1, 0, 0), coin.SoMarkerSet.DIAMOND_FILLED_9_9)
    markerSep.color = [(1, 0, 0)] + [(0.5, 0.0, 0.5)] * (len(flatPoles) - 1)

    u0, u1, v0, v1 = surf.bounds()
    halfU = u0 + (u1 - u0) / 2
    halfV = v0 + (v1 - v0) / 2
    UPos = surf.value(halfU, v0)
    Uletter = coinNodes.text2dNode((0, 0, 0),
                                   "osiFont,FreeSans,sans",
                                   20,
                                   (UPos.x, UPos.y, UPos.z),
                                   'U')
    VPos = surf.value(u0, halfV)
    Vletter = coinNodes.text2dNode((0, 0, 0),
                                   "osiFont,FreeSans,sans",
                                   20,
                                   (VPos.x, VPos.y, VPos.z),
                                   'V')

    vizSep = coin.SoSeparator()
    vizSep.addChild(polesnode)
    vizSep.addChild(polyRowSep)
    vizSep.addChild(polyColSep)
    vizSep.addChild(markerSep)
    vizSep.addChild(Uletter)
    vizSep.addChild(Vletter)
    if rational:
        # *** Set weight text ***
        weightSep = coinNodes.multiTextNode((1, 0, 0),
                                            "osiFont,FreeSans,sans",
                                            16, 0)
        weightSep.data = (flatPoles, weightStr)
        vizSep.addChild(weightSep)

    if bspline:
        color = (1.0, 0.5, 0.3)
        for k in uknots:
            try:
                uIso = surf.uIso(k)
                if uIso.length() > TOL3D:
                    ush = uIso.toShape()
                    uiso_node = edge_node(ush, color, 3)
                    vizSep.addChild(uiso_node)
                    # nb_curves += 1
                    color = (0.7, 0.0, 0.3)
            except Exception as exc:
                debug(f"Error computing surface U Iso\n{exc}")

        color = (0.8, 0.8, 0.0)
        for k in vknots:
            try:
                vIso = surf.vIso(k)
                if vIso.length() > TOL3D:
                    vsh = vIso.toShape()
                    viso_node = edge_node(vsh, color, 3)
                    vizSep.addChild(viso_node)
                    # nb_curves += 1
                    color = (0.3, 0.0, 0.7)
            except Exception as exc:
                debug(f"Error computing surface V Iso\n{exc}")

    return vizSep


class GeomNode:
    def __init__(self):
        self.node = coin.SoSeparator()
        view_param = FreeCAD.ParamGet("User parameter:View")
        AxisXcolor = view_param.GetUnsigned('AxisXColor', 0xff000000)
        AxisYcolor = view_param.GetUnsigned('AxisYColor', 0x00ff0000)
        AxisZcolor = view_param.GetUnsigned('AxisZColor', 0x0000ff00)
        curves_param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves")
        Ucolor = curves_param.GetUnsigned('GeomInfoColorU', AxisXcolor)
        Vcolor = curves_param.GetUnsigned('GeomInfoColorV', AxisYcolor)
        Wcolor = curves_param.GetUnsigned('GeomInfoColorW', AxisZcolor)
        self.Xcolor = self.hex_to_color(Ucolor)
        self.Ycolor = self.hex_to_color(Vcolor)
        self.Zcolor = self.hex_to_color(Wcolor)
        self.lineWidth = 1
        self.linePattern = 0xffff

    def hex_to_color(self, color):
        hex_string = f"{color:08x}"
        r = hex_string[0:2]
        g = hex_string[2:4]
        b = hex_string[4:6]
        return int(r, 16) / 255, int(g, 16) / 255, int(b, 16) / 255


class curveNode(GeomNode):
    "Coin3D node that displays curve data of an edge"

    def __init__(self, edge):
        super().__init__()
        self.edge = edge
        self.build_node()

    def build_node(self):
        # color = coinNodes.colorNode((0.7, 0.7, 1.0))
        # self.node.addChild(color)
        curve = self.edge.Curve
        if hasattr(curve, "Axis") and hasattr(curve, "Center"):
            culen = self.edge.Length / 2
            axis_end = curve.Axis * culen
            axis = Part.makeLine(curve.Center, curve.Center + axis_end)
            axis_node = edge_node(axis, self.Zcolor, self.lineWidth, self.linePattern)
            self.node.addChild(axis_node)
        if isinstance(curve, (Part.BezierCurve, Part.BSplineCurve)):
            self.node.addChild(bsplinecurveNode(curve))
            return
        if curve.isPeriodic():
            edge = curve.toShape()
        else:
            efp, elp = self.edge.ParameterRange
            try:
                fp = curve.parameterAtDistance(-self.edge.Length, efp)
                lp = curve.parameterAtDistance(self.edge.Length, elp)
            except Part.OCCError:  # Hyperbola
                ext_range = (elp - efp) * 1.0
                fp = max(efp - ext_range, curve.FirstParameter)
                lp = min(elp + ext_range, curve.LastParameter)
                print(fp, lp)
            edge = curve.toShape(fp, lp)
        curve_node = edge_node(edge, self.Xcolor, self.lineWidth, self.linePattern)
        self.node.addChild(curve_node)


class surfNode(GeomNode):
    "Coin3D node that displays surface data of a face"

    def __init__(self, face):
        super().__init__()
        self.face = face
        curves_param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves")
        self.num_iso = curves_param.GetInt('GeomInfoNumIso', 20)
        self.build_node()

    def build_node(self):
        surf = self.face.Surface
        if hasattr(surf, "Axis") and hasattr(surf, "Center"):
            u0, u1, v0, v1 = self.face.ParameterRange
            axis = Part.makeLine(surf.Center, surf.Center + surf.Axis)
            par1 = axis.Curve.parameter(surf.value(u0, v0))
            par2 = axis.Curve.parameter(surf.value(u1, v1))
            p1 = min(par1, par2)
            p2 = max(par1, par2)
            axis_pr = p2 - p1
            axis = axis.Curve.toShape(p1 - axis_pr * 2, p2 + axis_pr * 2)
            axis_node = edge_node(axis, self.Zcolor, self.lineWidth, self.linePattern)
            self.node.addChild(axis_node)
        if isinstance(surf, (Part.BezierSurface, Part.BSplineSurface)):
            self.node.addChild(bsplinesurfNode(surf))
            return
        ts = TrimmedSurface(self.face)
        ts.extend()
        ts.extend(1, Relative=True)
        tsurf = ts.Surface
        upars = paramList(self.num_iso, *ts.Bounds[:2])
        vpars = paramList(self.num_iso, *ts.Bounds[2:])
        color = (1.0, 0.5, 0.3)
        width = 3
        for u in upars:
            uiso = tsurf.uIso(u)
            # Part.show(uiso.toShape(*ts.Bounds[2:]))
            self.node.addChild(edge_node(uiso.toShape(), color, width, self.linePattern))
            color = self.Xcolor
            width = self.lineWidth
        color = (0.3, 0.5, 1.0)
        width = 3
        for v in vpars:
            viso = tsurf.vIso(v)
            # Part.show(viso.toShape(*ts.Bounds[:2]))
            self.node.addChild(edge_node(viso.toShape(), color, width, self.linePattern))
            color = self.Ycolor
            width = self.lineWidth


class HUDNode:
    def __init__(self):
        curves_param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves")
        left_margin = curves_param.GetFloat('GeomInfoLeftMargin', 0.02)
        top_margin = curves_param.GetFloat('GeomInfoTopMargin', 0.1)
        f_name = curves_param.GetString('GeomInfoFontString', "FreeMono,FreeSans,sans")
        size = curves_param.GetInt('GeomInfoFontSize', 14)
        pref_col = curves_param.GetString('GeomInfoFontColor', "0,0,0")

        self.node = coin.SoSeparator()
        self.cam = coin.SoOrthographicCamera()
        self.cam.aspectRatio = 1
        self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE

        self.trans = coin.SoTranslation()
        self.trans.translation = (-1.0 + left_margin * 2, 1.0 - top_margin * 2, 0)

        self.myFont = coin.SoFont()
        self.myFont.name = f_name
        self.myFont.size.setValue(size)
        self.SoText2 = coin.SoText2()
        self.SoText2.string = ""
        color = tuple([float(x) for x in pref_col.split(',')])
        self.color = coin.SoBaseColor()
        self.color.rgb = color

        self.node.addChild(self.cam)
        self.node.addChild(self.trans)
        self.node.addChild(self.color)
        self.node.addChild(self.myFont)
        self.node.addChild(self.SoText2)

    def set_text(self, txt):
        if isinstance(txt, str):
            self.SoText2.string = txt
        elif isinstance(txt, (list, tuple)):
            self.SoText2.string.setValues(0, len(txt), txt)


class GeomInfo:
    "this class displays info about the geometry of the selected shape"

    def __init__(self):
        self.pat = re.compile(r"<([a-zA-Z_][a-zA-Z0-9_]*) object>")

    def Activated(self, index=0):

        if index == 1:
            debug("GeomInfo activated")
            self.stack = []
            # install the function in resident mode
            FreeCADGui.Selection.addObserver(self)
            self.active = True
            self.hud = HUDNode()
            self.addHUD()
            self.Active = True
            self.viz = False
            self.getTopo()

        elif (index == 0) and self.Active:
            debug("GeomInfo off")
            self.removeHUD()
            self.Active = False
            FreeCADGui.Selection.removeObserver(self)

    def addHUD(self):
        try:
            self.activeDoc = FreeCADGui.ActiveDocument
            self.view = self.activeDoc.ActiveView
            self.sg = self.view.getSceneGraph()
            self.viewer = self.view.getViewer()
            self.render = self.viewer.getSoRenderManager()
            self.sup = self.render.addSuperimposition(self.hud.node)
            self.sg.touch()
        except AttributeError:
            self.activeDoc = None

    def removeHUD(self):
        try:
            if str(self.activeDoc):
                self.render.removeSuperimposition(self.sup)
                self.removeGrid()
                self.sg.touch()
        except ReferenceError:
            debug("GeomInfo: doc has been closed")

    def removeGrid(self):
        if self.viz:
            self.root.removeChild(self.node)
            self.viz = False

    def insertGrid(self):
        if self.node:
            self.root.addChild(self.node)
            self.viz = True

# ------ Selection Observer --------

    def addSelection(self, doc, obj, sub, pnt):
        if self.Active:
            if not doc == self.activeDoc:
                self.removeHUD()
                self.addHUD()
            self.getTopo()

    def removeSelection(self, doc, obj, sub):
        if self.Active:
            self.hud.set_text("")
            self.removeGrid()

    def setPreselection(self, doc, obj, sub):
        pass

    def clearSelection(self, doc):  # If screen is clicked, delete selection
        if self.Active:
            self.hud.set_text("")
            self.removeGrid()

# ------ get info about shape --------

    def propStr(self, c, att):
        if hasattr(c, att):
            a = c.__getattribute__(att)
            if callable(a):
                a = a()
            if not a:
                return False
            elif hasattr(a, 'x') and hasattr(a, 'y') and hasattr(a, 'z'):
                return "%s : (%0.2f, %0.2f, %0.2f)" % (att, a.x, a.y, a.z)
            else:
                return "%s : %s" % (att, str(a))
        else:
            return False

    def getSurfInfo(self, face):
        surf = face.Surface
        ret = []
        ret.append(extract_name(surf))
        props = ['Center',
                 'Axis',
                 'Position',
                 'Radius',
                 'Direction',
                 'Location',
                 'Continuity']
        for p in props:
            s = self.propStr(surf, p)
            if s:
                ret.append(s)
        if isinstance(surf, (Part.BSplineSurface, Part.BezierSurface)):
            ret.append("Degree : %d x %d" % (surf.UDegree, surf.VDegree))
            ret.append("Poles  : %d x %d (%d)" % (surf.NbUPoles,
                                                  surf.NbVPoles,
                                                  surf.NbUPoles * surf.NbVPoles))
        props = ['isURational',
                 'isVRational',
                 'isUPeriodic',
                 'isVPeriodic',
                 'isUClosed',
                 'isVClosed']
        for p in props:
            s = self.propStr(surf, p)
            if s:
                ret.append(s)
        pl = surf.isPlanar()
        if pl:
            s = "is Planar"
            ret.append(s)
        if isinstance(surf, Part.BSplineSurface):
            funct = [(surf.getUKnots, "U Knots"),
                     (surf.getUMultiplicities, "U Mults"),
                     (surf.getVKnots, "V Knots"),
                     (surf.getVMultiplicities, "V Mults")]
            for i in funct:
                r = i[0]()
                if r:
                    s = str(i[1]) + " : " + numbers_to_str(r)
                    ret.append(s)
        if hasattr(face, 'getTolerance'):
            s = "Shape Tolerance : {}".format(face.getTolerance(1))
            ret.append(s)
        return ret

    def _formatObj(self, obj):
        str_val = str(obj)
        if match := self.pat.match(str_val):
            return match.group(1)
        return str_val

    def getCurvInfo(self, edge):
        curve = edge.Curve
        ret = []
        ret.append(extract_name(curve))
        props = ['Center',
                 'Axis',
                 'Position',
                 'Radius',
                 'Direction',
                 'Location',
                 'Degree',
                 'NbPoles',
                 'Continuity']
        for p in props:
            s = self.propStr(curve, p)
            if s:
                ret.append(s)
        props = ['isRational', 'isPeriodic', 'isClosed']
        for p in props:
            s = self.propStr(curve, p)
            if s:
                ret.append(s)
        if hasattr(curve, 'getKnots'):
            r = curve.getKnots()
            s = "Knots : " + numbers_to_str(r)
            ret.append(s)
        if hasattr(curve, 'getMultiplicities'):
            r = curve.getMultiplicities()
            s = "Mults : " + numbers_to_str(r)
            ret.append(s)
        if hasattr(edge, 'Length'):
            r = edge.Length
            s = "Length : {:3.3f}".format(r)
            try:
                le = curve.length()
                if not le == r and le < 1e20:
                    s += " ({:3.3f})".format(le)
            except (AttributeError, Part.OCCError):
                pass
            ret.append(s)
            # else:
            #     ret.append("Length : Infinite")
        if hasattr(edge, 'getTolerance'):
            s = "Shape Tolerance : {}".format(edge.getTolerance(1))
            ret.append(s)
        pclist = _utils.get_pcurves(edge)
        for pc in pclist:
            s = "{} on {} ".format(self._formatObj(pc[0]),
                                   self._formatObj(pc[1]))
            ret.append(s)
        return ret

    def getTopo(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel != []:
            sel0 = sel[0]
            if sel0.HasSubObjects:
                try:
                    self.ss = sel0.SubObjects[-1]
                    self.so = sel0.Object
                except Exception as exc:
                    debug(f"{exc}")
                    return
            else:
                return
            if self.ss.isNull():
                return
            t = ""
            if self.ss.ShapeType == 'Face':
                t = self.getSurfInfo(self.ss)
                self.node = surfNode(self.ss).node
            elif self.ss.ShapeType == 'Edge':
                t = self.getCurvInfo(self.ss)
                self.node = curveNode(self.ss).node
            self.hud.set_text(t)
            self.removeGrid()
            self.root = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
            self.insertGrid()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}\n\n{}\n\n{}".format(__title__, __doc__, __usage__),
                'Checkable': False}


FreeCADGui.addCommand('GeomInfo', GeomInfo())
