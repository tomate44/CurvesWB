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


TOOL_ICON = os.path.join(ICONPATH, 'info.svg')
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


def beautify(shp):
    if not shp:
        return ""
    else:
        t = shp
        if (shp[0] == "<") and (shp[-1] == ">"):
            t = shp[1:-1]
        return t.split()[0]


def getString(weights):
    weightStr = []
    for w in weights:
        if abs(w - 1.0) < 0.001:
            weightStr.append("")
        elif w.is_integer():
            weightStr.append(" %d" % int(w))
        else:
            weightStr.append(" %0.2f" % w)
    return weightStr


def cleanString(arr):
    strArr = ""
    if len(arr) > 20:
        return cleanString(arr[0:10]) + " ... " + cleanString(arr[-10:])
    for w in arr:
        if isinstance(w, float):
            strArr += "%0.2f, " % w
        else:
            strArr += "%d, " % int(w)
    return strArr[:-2]


def coordStr(v):
    if hasattr(v, 'x'):
        s = "%0.2f" % v.x
        if hasattr(v, 'y'):
            s += ", %0.2f" % v.y
            if hasattr(v, 'z'):
                s += ", %0.2f" % v.z
        return s
    else:
        return v


def removeDecim(arr):
    r = []
    for fl in arr:
        r.append("%0.2f" % fl)
    return r


def to1D(arr):
    array = []
    for row in arr:
        for el in row:
            array.append(el)
    return array


def paramList(n, fp, lp):
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


def curveNode(cur):
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
    weightStr = getString(weights)

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


def surfNode(surf):
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
    weightStr = getString(flatW)

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

        # *** Set knots ***
        uknotPoints = []
        nb_curves = 0
        np = 100
        for k in uknots:
            try:
                uIso = surf.uIso(k)
                if uIso.length() > TOL3D:
                    epts = uIso.toShape().discretize(np)
                    for p in epts:
                        uknotPoints.append((p.x, p.y, p.z))
                    nb_curves += 1
            except Exception as exc:
                debug(f"Error computing surface U Iso\n{exc}")

        if nb_curves > 0:
            uknotsnode = coinNodes.coordinate3Node(uknotPoints)
            uCurves = coinNodes.rowNode((1.0, 0.5, 0.3), 3)
            uCurves.color = [(1.0, 0.5, 0.3)] * (np - 1)
            uCurves.color += [(0.7, 0.0, 0.3)] * (nb_curves - 1) * (np - 1)
            uCurves.vertices = (nb_curves, np)
            vizSep.addChild(uknotsnode)
            vizSep.addChild(uCurves)

        vknotPoints = []
        nb_curves = 0
        for k in vknots:
            try:
                vIso = surf.vIso(k)
                if vIso.length() > TOL3D:
                    epts = vIso.toShape().discretize(np)
                    for p in epts:
                        vknotPoints.append((p.x, p.y, p.z))
                    nb_curves += 1
            except Exception as exc:
                debug(f"Error computing surface V Iso\n{exc}")

        if nb_curves > 0:
            vknotsnode = coinNodes.coordinate3Node(vknotPoints)
            vCurves = coinNodes.rowNode((0.3, 0.5, 1.0), 3)
            vCurves.color = [(0.8, 0.8, 0.0)] * (np - 1)
            vCurves.color += [(0.3, 0.0, 0.7)] * (nb_curves - 1) * (np - 1)
            vCurves.vertices = (nb_curves, np)
            vizSep.addChild(vknotsnode)
            vizSep.addChild(vCurves)

        # removed because of several FC crashes
#         # ***** isoCurves ******
#
#         uparam = paramList(16,u0,u1)
#         uisoPoints = []
#         nb_curves = 0
#         for k in uparam:
#             try:
#                 uIso = surf.uIso(k)
#                 epts = uIso.toShape().discretize(100)
#                 if len(epts) == 100:
#                     for p in epts:
#                         uisoPoints.append((p.x,p.y,p.z))
#                     nb_curves += 1
#             except:
#                 debug("Error computing surface U Iso")
#
#         if nb_curves > 0:
#             uisonode = coinNodes.coordinate3Node(uisoPoints)
#             uisoCurves = coinNodes.rowNode((0.0,0.0,0.0),1)
#             uisoCurves.transparency = 0.8
#             uisoCurves.vertices=(nb_curves,100)
#             vizSep.addChild(uisonode)
#             vizSep.addChild(uisoCurves)
#             #debug(str(uCurves.vertices))
#
#         vparam = paramList(16,v0,v1)
#         visoPoints = []
#         nb_curves = 0
#         for k in vparam:
#             try:
#                 vIso = surf.vIso(k)
#                 epts = vIso.toShape().discretize(100)
#                 if len(epts) == 100:
#                     for p in epts:
#                         vknotPoints.append((p.x,p.y,p.z))
#                     nb_curves += 1
#             except:
#                 debug("Error computing surface V Iso")
#
#         if nb_curves > 0:
#             visonode = coinNodes.coordinate3Node(visoPoints)
#             visoCurves = coinNodes.rowNode((0.0,0.0,0.0),1)
#             visoCurves.transparency = 0.8
#             visoCurves.vertices=(nb_curves,100)
#             vizSep.addChild(visonode)
#             vizSep.addChild(visoCurves)
#
#         # *** Set texts ***
#         multStr = []
#         for m in mults:
#             multStr.append("%d"%m)
#
#         knotMarkerSep = coinNodes.markerSetNode((0,0,1),coin.SoMarkerSet.CIRCLE_FILLED_9_9)
#
#         # *** Set mult text ***
#         multSep = coinNodes.multiTextNode((0,0,1),"osiFont,FreeSans,sans",16,1)
#         multSep.data = (knotPoints,multStr)

    return vizSep


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
            self.textSep = coin.SoSeparator()
            self.cam = coin.SoOrthographicCamera()
            self.cam.aspectRatio = 1
            self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE

            self.trans = coin.SoTranslation()
            left_margin = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves").GetFloat('GeomInfoLeftMargin', 0.02)
            top_margin = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves").GetFloat('GeomInfoTopMargin', 0.1)
            self.trans.translation = (-1.0 + left_margin * 2, 1.0 - top_margin * 2, 0)

            self.myFont = coin.SoFont()
            f_name = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves").GetString('GeomInfoFontString', "FreeMono,FreeSans,sans")
            self.myFont.name = f_name
            size = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves").GetInt('GeomInfoFontSize', 14)
            # print(size)
            self.myFont.size.setValue(size)
            self.SoText2 = coin.SoText2()
            self.SoText2.string = ""  # "Nothing Selected\r2nd line"
            pref_col = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Curves").GetString('GeomInfoFontColor', "0,0,0")
            color = tuple([float(x) for x in pref_col.split(',')])
            self.color = coin.SoBaseColor()
            self.color.rgb = color

            self.textSep.addChild(self.cam)
            self.textSep.addChild(self.trans)
            self.textSep.addChild(self.color)
            self.textSep.addChild(self.myFont)
            self.textSep.addChild(self.SoText2)

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
            self.sup = self.render.addSuperimposition(self.textSep)
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

    def addSelection(self, doc, obj, sub, pnt):  # Selection
        # FreeCAD.Console.PrintMessage("addSelection %s %s\n" % (obj, str(sub)))
        if self.Active:
            if not doc == self.activeDoc:
                self.removeHUD()
                self.addHUD()
            self.getTopo()

    def removeSelection(self, doc, obj, sub):  # Delete selected object
        # FreeCAD.Console.PrintMessage("removeSelection %s %s\n" % (obj, str(sub)))
        if self.Active:
            self.SoText2.string = ""
            self.removeGrid()

    def setPreselection(self, doc, obj, sub):
        pass

    def clearSelection(self, doc):  # If screen is clicked, delete selection
        # FreeCAD.Console.PrintMessage("clearSelection\n")
        if self.Active:
            self.SoText2.string = ""
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

    # def propMeth(self, c, att):
    #     if hasattr(c, att):
    #         a = c.__getattribute__(att)()
    #         if not a:
    #             return False
    #         elif hasattr(a, 'x') and hasattr(a, 'y') and hasattr(a, 'z'):
    #             return "%s : (%0.2f, %0.2f, %0.2f)" % (att, a.x, a.y, a.z)
    #         else:
    #             return "%s : %s"%(att, str(a))
    #     else:
    #         return False

    def getSurfInfo(self, face):
        surf = face.Surface
        ret = []
        ret.append(beautify(str(surf)))
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
                    s = str(i[1]) + " : " + cleanString(r)
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
        ret.append(beautify(str(curve)))
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
            s = "Knots : " + cleanString(r)
            ret.append(s)
        if hasattr(curve, 'getMultiplicities'):
            r = curve.getMultiplicities()
            s = "Mults : " + cleanString(r)
            ret.append(s)
        if hasattr(edge, 'Length'):
            r = edge.Length
            s = "Length : {:3.3f}".format(r)
            if hasattr(curve, 'length'):
                le = curve.length()
                if not le == r and le < 1e20:
                    s += " ({:3.3f})".format(le)
                ret.append(s)
            else:
                ret.append("Length : Infinite")
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
            if self.ss.ShapeType == 'Face':
                surf = self.ss.Surface
                t = self.getSurfInfo(self.ss)
                self.SoText2.string.setValues(0, len(t), t)
                self.removeGrid()
                self.root = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
                self.node = surfNode(surf)
                self.insertGrid()
            elif self.ss.ShapeType == 'Edge':
                cur = self.ss.Curve
                t = self.getCurvInfo(self.ss)
                self.SoText2.string.setValues(0, len(t), t)
                self.removeGrid()
                self.root = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
                self.node = curveNode(cur)
                self.insertGrid()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': "{}\n\n{}\n\n{}".format(__title__, __doc__, __usage__),
                'Checkable': False}


FreeCADGui.addCommand('GeomInfo', GeomInfo())
