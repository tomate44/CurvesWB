# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import FreeCAD
import FreeCADGui
# import Part
# from FreeCAD import Base
from pivy import coin
from freecad.Curves import libS2R
from freecad.Curves import CoinNodes
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'sw2r.svg')
fac = 1.0
DEBUG = False


def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class sweep2rails:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink",       "Birail",         "Base",   "Birail object")
        obj.addProperty("App::PropertyLinkList",   "Profiles",       "Base",   "List of profiles")
        obj.addProperty("App::PropertyEnumeration","Blending",       "Base",   "Blending method").Blending = ["Average","Blend","Rail1","Rail2"]
        obj.addProperty("App::PropertyFloat",      "Parametrization","Base",   "Parametrization of interpolating curves")
        obj.addProperty("App::PropertyInteger",    "ProfileSamples", "Base",   "Profile Samples")
        obj.addProperty("App::PropertyInteger",    "RailSamples",    "Base",   "Profile Samples")
        obj.addProperty("App::PropertyBool",       "Extend",         "Base",   "Extend to rail limits")
        obj.addProperty("App::PropertyVectorList", "Points",         "Base",   "Points")
        obj.addProperty("Part::PropertyPartShape", "Shape",          "Base",   "Shape")
        obj.Blending = "Blend"
        obj.ProfileSamples = 20
        obj.RailSamples = 20
        obj.Parametrization = 0.0
        obj.Extend = False

    def execute(self, obj):
        if hasattr(obj, "Birail") and hasattr(obj, "Profiles"):
            if (obj.Birail is not None) and (not obj.Profiles == []):
                s2r = libS2R.SweepOn2Rails()
                s2r.parametrization = obj.Parametrization
                s2r.extend = obj.Extend
                s2r.profileSamples = obj.ProfileSamples
                s2r.railSamples = obj.RailSamples
                s2r.setRails(obj.Birail.Shape.Face1)
                s2r.setProfiles(self.setProfiles(obj.Profiles))  # ((e1,e2,e3))
                s2r.build()
                # s2r.showLocalProfiles()
                # s2r.showInterpoCurves()
                s2r.mix(obj.Blending)
                # s2r.show()
                obj.Points = s2r.downgradeArray()
                obj.Shape = s2r.shapeCloud()
                return s2r

    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage('{} changed\n'.format(prop))
        if prop == "Birail":
            pass
        if prop == "Profiles":
            pass
        if prop == "Blending":
            pass
        if prop == "ProfileSamples":
            if fp.ProfileSamples < 2:
                fp.ProfileSamples = 2
            elif fp.ProfileSamples > 500:
                fp.ProfileSamples = 500
        if prop == "RailSamples":
            if fp.RailSamples < 2:
                fp.RailSamples = 2
            elif fp.RailSamples > 1000:
                fp.RailSamples = 1000
            # n = len(fp.Profiles) - 1
            # gr = int(1.0 * fp.RailSamples / n) + 1
            # fp.RailSamples = gr * n

    def setProfiles(self, prop):
        a = []
        for obj in prop:
            a.append(obj.Shape.Edges[0])
        return a


class sweep2railsVP:
    def __init__(self, obj):
        obj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        # self.ViewObject = vobj
        self.Object = vobj.Object

        self.gridDM = coin.SoGroup()
        self.pointsDM = coin.SoGroup()
        self.ProfDM = coin.SoGroup()
        self.railDM = coin.SoGroup()
        self.coord = CoinNodes.coordinate3Node(self.Object.Points)
        self.row = CoinNodes.rowNode((0.8, 0.4, 0.4), 1.0)
        self.col = CoinNodes.colNode((0.4, 0.4, 0.8), 1.0)
        self.pointSet = coin.SoPointSet()
        self.style = CoinNodes.styleNode((0, 0, 0), 1.0, 2.0)
        self.style.addChild(self.pointSet)
        # vobj.addChild(self.coord)
        self.ProfDM.addChild(self.coord)
        self.ProfDM.addChild(self.row)
        self.railDM.addChild(self.coord)
        self.railDM.addChild(self.col)
        self.gridDM.addChild(self.coord)
        self.gridDM.addChild(self.row)
        self.gridDM.addChild(self.col)
        self.pointsDM.addChild(self.coord)
        self.pointsDM.addChild(self.style)
        # self.points.addChild(self.pointSet)
        vobj.addDisplayMode(self.gridDM, "Wireframe")
        vobj.addDisplayMode(self.pointsDM, "Points")
        vobj.addDisplayMode(self.ProfDM, "Profiles")
        vobj.addDisplayMode(self.railDM, "Rails")
        # self.onChanged(vobj, "DisplayMode")
        # if "Wireframe" in vobj.listDisplayModes():
        # vobj.DisplayMode = "Wireframe"

    def updateData(self, fp, prop):
        FreeCAD.Console.PrintMessage("updateDate : " + str(prop) + "\n")
        if len(fp.Points) == fp.RailSamples * fp.ProfileSamples:
            self.coord.points = fp.Points
            self.row.vertices = (fp.RailSamples, fp.ProfileSamples)
            self.col.vertices = (fp.RailSamples, fp.ProfileSamples)

    def onChanged(self, vp, prop):
        "Here we can do something when a single property got changed"
        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def getDisplayModes(self, obj):
        "Return a list of display modes."
        modes = []
        modes.append("Points")
        modes.append("Profiles")
        modes.append("Rails")
        modes.append("Wireframe")
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode.
        It must be defined in getDisplayModes."""
        return "Points"

    def setDisplayMode(self, mode):
        return mode

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
        a = self.Object.Profiles
        a.append(self.Object.Birail)
        return a

    def onDelete(self, feature, subelements):
        try:
            self.Object.Birail.ViewObject.show()
            for p in self.Object.Profiles:
                p.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        return True


class s2rCommand:
    def parseSel(self, selectionObject):
        birail = None
        profs = []
        for obj in selectionObject:
            if hasattr(obj, "NormalizeBinormal") or hasattr(obj, "Orientation"):
                birail = obj
            else:
                profs.append(obj)
        return (birail, profs)

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s == []:
            FreeCAD.Console.PrintError("Select a ruled surface and a list of profile edges\n")
            return
        myS2R = FreeCAD.ActiveDocument.addObject("App::FeaturePython",
                                                 "Sweep 2 rails")
        sweep2rails(myS2R)
        sweep2railsVP(myS2R.ViewObject)

        myS2R.Birail = self.parseSel(s)[0]
        myS2R.Profiles = self.parseSel(s)[1]
        myS2R.Birail.ViewObject.Visibility = False
        for p in myS2R.Profiles:
            p.ViewObject.Visibility = False

        # myS2R.ViewObject.PointSize = 2.00000
        # myS2R.ViewObject.LineColor = (0.0,0.0,0.7)
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Sweep2Rails',
                'ToolTip': 'Sweep profiles on 2 rails'}


FreeCADGui.addCommand('sw2r', s2rCommand())
