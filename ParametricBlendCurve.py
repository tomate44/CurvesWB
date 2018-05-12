# -*- coding: utf-8 -*-

__title__ = "Blend curve"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Blend curve between two edges."

import FreeCAD
import FreeCADGui
import Part
import _utils

from pivy import coin
import nurbs_tools
import CoinNodes

TOOL_ICON = _utils.iconsPath() + '/blend.svg'
debug = _utils.debug
#debug = _utils.doNothing

class BlendCurveFP:
    def __init__(self, obj , edges):
        debug("BlendCurve class Init")
        
        obj.addProperty("App::PropertyLinkSub",         "Edge1",      "Edge1", "Edge 1").Edge1 = edges[0]
        obj.addProperty("App::PropertyLinkSub",         "Edge2",      "Edge2", "Edge 2").Edge2 = edges[1]
        obj.addProperty("App::PropertyInteger",         "DegreeMax",  "BlendCurve", "Max degree of the Blend curve").DegreeMax = 9
        obj.addProperty("App::PropertyFloatConstraint", "Parameter1", "Edge1", "Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint", "Scale1",     "Edge1", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration",     "Continuity1","Edge1", "Continuity").Continuity1=["C0","G1","G2","G3","G4"]
        obj.addProperty("App::PropertyFloatConstraint", "Parameter2", "Edge2", "Location of blend curve")
        obj.addProperty("App::PropertyFloatConstraint", "Scale2",     "Edge2", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration",     "Continuity2","Edge2", "Continuity").Continuity2=["C0","G1","G2","G3","G4"]
        obj.addProperty("App::PropertyVectorList",      "CurvePts",   "BlendCurve", "CurvePts")
        obj.addProperty("App::PropertyEnumeration",     "Output",     "BlendCurve", "Output type").Output=["Wire","Joined","Single"]
        obj.Scale1 = (1.,-5.0,5.0,0.05)
        obj.Scale2 = (1.,-5.0,5.0,0.05)
        obj.Parameter1 = ( 1.0, 0.0, 1.0, 0.05 )
        obj.Parameter2 = ( 1.0, 0.0, 1.0, 0.05 )
        obj.Proxy = self

    def execute(self, fp):
        e1 = _utils.getShape(fp, "Edge1", "Edge")
        e2 = _utils.getShape(fp, "Edge2", "Edge")
        if e1 and e2:
            bc = nurbs_tools.blendCurve(e1,e2)
            bc.param1 = e1.FirstParameter + fp.Parameter1 * (e1.LastParameter - e1.FirstParameter)
            bc.param2 = e2.FirstParameter + fp.Parameter2 * (e2.LastParameter - e2.FirstParameter)
            bc.cont1 = self.getContinuity(fp.Continuity1)
            bc.cont2 = self.getContinuity(fp.Continuity2)
            bc.scale1 = fp.Scale1
            bc.scale2 = fp.Scale2
            bc.maxDegree = fp.DegreeMax
            bc.compute()
            fp.CurvePts = bc.Curve.getPoles()
            if fp.Output == "Wire":
                fp.Shape = bc.getWire()
            elif fp.Output == "Joined":
                fp.Shape = bc.getJoinedCurve().toShape()
            else:
                fp.Shape = bc.Curve.toShape()

    def onChanged(self, fp, prop):
        if prop == "Scale1":
            if fp.Scale1 == 0:
                fp.Scale1 = 0.0001
            self.execute(fp)
        elif prop == "Scale2":
            if fp.Scale2 == 0:
                fp.Scale2 = 0.0001
            self.execute(fp)
        elif prop in ("Parameter1","Parameter2"):
            self.execute(fp)
        elif prop == "DegreeMax":
            if fp.DegreeMax < 1:
                fp.DegreeMax = 1
            elif fp.DegreeMax > 9:
                fp.DegreeMax = 9

    def onDocumentRestored(self, fp):
        debug("%s restored !"%fp.Label)
        fp.Scale1 = (fp.Scale1,-5.0,5.0,0.05)
        fp.Scale2 = (fp.Scale2,-5.0,5.0,0.05)
        fp.Parameter1 = ( fp.Parameter1, 0.0, 1.0, 0.05 )
        fp.Parameter2 = ( fp.Parameter2, 0.0, 1.0, 0.05 )

    def getContinuity(self, cont):
        if cont == "C0":
            return(0)
        elif cont == "G1":
            return(1)
        elif cont == "G2":
            return(2)
        elif cont == "G3":
            return(3)
        else:
            return(4)


class BlendCurveVP:
    def __init__(self, obj ):
        debug("VP init")
        obj.Proxy = self
        self.build()
        #self.children = []

    def claimChildren(self):
        if hasattr(self,"children"):
            return(self.children)
        else:
            return([])

    def build(self):
        self.active = False
        if not hasattr(self,'switch'):
            self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
            self.switch = coin.SoSwitch()
            if hasattr(self,'Object'):
                self.switch.setName("%s_ControlPoints"%self.Object.Name)
            self.empty = coin.SoSeparator() # Empty node
            self.node = coin.SoSeparator()
            self.coord = CoinNodes.coordinate3Node()
            self.poly = CoinNodes.polygonNode((0.5,0.5,0.5),1)
            self.marker = CoinNodes.markerSetNode((1,0,0),coin.SoMarkerSet.DIAMOND_FILLED_7_7)
            self.node.addChild(self.coord)
            self.node.addChild(self.poly)
            self.node.addChild(self.marker)
            self.switch.addChild(self.empty)
            self.switch.addChild(self.node)
            self.sg.addChild(self.switch)

    def setVisi(self, objs, vis):
        for o in objs:
            o.ViewObject.Visibility = vis

    def attach(self, vobj):
        debug("VP attach")
        self.Object = vobj.Object
        self.children = []
        #self.claimed = False

    def updateData(self, fp, prop):
        if prop == "CurvePts":
            if hasattr(self,'coord') and hasattr(self,'poly'):
                self.coord.points = fp.CurvePts
                self.poly.vertices = self.coord.points
        elif prop == "Output":
            if fp.Output in ("Wire","Joined"):
                if self.children == []:
                    self.children = [fp.Edge1[0], fp.Edge2[0]]
                    self.setVisi(self.children, False)
                    #self.claimed = True
            else:
                if not self.children == []:
                    self.setVisi(self.children, True)
                    #self.claimed = True
                    self.children = []

    def doubleClicked(self,vobj):
        if not hasattr(self,'active'):
            self.active = False
        if not self.active:
            self.active = True
            self.switch.whichChild = 1
        else:
            self.active = False
            self.switch.whichChild = 0
        return(True)

    def setEdit(self,vobj,mode):
        debug("Start Edit")
        return(True)

    def unsetEdit(self,vobj,mode):
        debug("End Edit")
        return(True)

    def getIcon(self):
        return(TOOL_ICON)

    def __getstate__(self):
        return({"name": self.Object.Name})

    def __setstate__(self,state):
        debug("setstate")
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        self.build()
        return(None)

    def onDelete(self, feature, subelements):
        if hasattr(self,'active'):
            if self.active:
                self.sg.removeChild(self.switch)
        return(True)

class ParametricBlendCurve:
    """Prepare selection and create blendCurve FeaturePython object."""
    def getEdge(self, edge):
        n = eval(edge[1].lstrip('Edge'))
        return(edge[0].Shape.Edges[n-1])

    def normalizedParam(self, edge, par, endClamp = False):
        e = self.getEdge(edge)
        goodpar = (par - e.FirstParameter) * 1.0 / (e.LastParameter - e.FirstParameter)
        if endClamp:
            if goodpar < 0.5:
                goodpar = 0.0
            else:
                goodpar = 1.0
        return(goodpar)

    def parseSel(self, selectionObject):
        res = []
        param = []
        for obj in selectionObject:
            for i in range(len(obj.SubObjects)):
                so = obj.SubObjects[i]
                if isinstance(so,Part.Edge):
                    res.append([obj.Object,obj.SubElementNames[i]])
                    p = obj.PickedPoints[i]
                    poe = so.distToShape(Part.Vertex(p))
                    par = poe[2][0][2]
                    param.append(par)
        return(res,param)

    def line(self, ed, p):
        e = self.getEdge(ed)
        pt = e.valueAt(p)
        t = e.tangentAt(p).multiply(100000)
        l = Part.LineSegment(pt,pt.add(t)).toShape()
        return(l)

    def getOrientation(self, e1, p1, e2, p2):
        r1 = -1.0
        r2 = -1.0
        l1 = self.line(e1, p1)
        l2 = self.line(e2, p2)
        dts = l1.distToShape(l2)
        par1 = dts[2][0][2]
        par2 = dts[2][0][5]
        if par1:
            r1 = 1.0
        if par2:
            r2 = 1.0
        return(r1,r2)

    def Activated(self):
        s = FreeCADGui.activeWorkbench().Selection
        edges, param = self.parseSel(s)
        if len(edges) > 1:
            for j in range(int(len(edges)/2)):
                i = j*2
                obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Blend Curve") #add object to document
                BlendCurveFP(obj,edges[i:i+2])
                BlendCurveVP(obj.ViewObject)
                obj.Parameter1 = self.normalizedParam(edges[i], param[i], True)
                obj.Parameter2 = self.normalizedParam(edges[i+1], param[i+1], True)
                obj.Continuity1 = "G1"
                obj.Continuity2 = "G1"
                obj.Output = "Single"
                ori1, ori2 = self.getOrientation(edges[i], param[i], edges[i+1], param[i+1])
                obj.Scale1 = ori1
                obj.Scale2 = ori2
        FreeCAD.ActiveDocument.recompute()

    def GetResources(self):
        return {'Pixmap' : TOOL_ICON, 'MenuText': 'ParametricBlendCurve', 'ToolTip': 'Creates a parametric blend curve'}

FreeCADGui.addCommand('ParametricBlendCurve', ParametricBlendCurve())



