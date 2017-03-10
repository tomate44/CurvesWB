import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import dummy
import CoinNodes as coinNodes
reload(coinNodes)


path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

def beautify(shp):
    if not shp:
        return ""
    else:
        if (shp[0] == "<") and (shp[-1] == ">"):
            t = shp[1:-1]
            return t.split()[0]
        else:
            return shp

def removeDecim(arr):
    r = []
    for fl in arr:
        r.append("%0.2f"%fl)
    return r

def curveNode(cur):
    try:
        poles = cur.getPoles()
        weights = cur.getWeights()
    except:
        return False
    try:
        knots = cur.getKnots()
        mults = cur.getMultiplicities()
        bspline = True
    except:
        bspline = False


    # *** Set poles ***    
    polesnode = coinNodes.coordinate3Node(poles)

    # *** Set weights ***    
    weightStr = []
    for w in weights:
        weightStr.append("%0.2f"%w)

    polySep = coinNodes.polygonNode((0,0,0),1)
    polySep.vertices = poles

    # *** Set markers ***    
    markerSep = coinNodes.markerSetNode((1,0,0),coin.SoMarkerSet.DIAMOND_FILLED_7_7)

    # *** Set weight text ***
    weightSep = coinNodes.multiTextNode((1,0,0),"osiFont,FreeSans,sans",16,(0,0,2))
    weightSep.data = (poles,weightStr)

    if bspline:

        # *** Set knots ***
        knotPoints = []
        for k in knots:
            p = cur.value(k)
            knotPoints.append((p.x,p.y,p.z))
        
        knotsnode = coinNodes.coordinate3Node(knotPoints)
        
        # *** Set texts ***        
        multStr = []
        for m in mults:
            multStr.append("%d"%m)
        
        knotMarkerSep = coinNodes.markerSetNode((0,0,1),coin.SoMarkerSet.CIRCLE_FILLED_9_9)

        # *** Set mult text ***        
        multSep = coinNodes.multiTextNode((0,0,1),"osiFont,FreeSans,sans",16,(0,0,-2))
        multSep.data = (knotPoints,multStr)

    vizSep = coin.SoSeparator()
    vizSep.addChild(polesnode)
    vizSep.addChild(polySep)
    vizSep.addChild(markerSep)
    vizSep.addChild(weightSep)
    if bspline:
        vizSep.addChild(knotsnode)
        vizSep.addChild(knotMarkerSep)
        vizSep.addChild(multSep)
    return vizSep

class GeomInfo:
    "this class displays info about the geometry of the selected topology"
    def Activated(self,index=0):

        if index == 1:
            print "GeomInfo activated"
            self.view = FreeCADGui.ActiveDocument.ActiveView
            self.stack = []
            FreeCADGui.Selection.addObserver(self)    # installe la fonction en mode resident
            #FreeCADGui.Selection.addObserver(self.getTopo)
            self.active = True
            self.sg = self.view.getSceneGraph()
            self.textSep = coin.SoSeparator()
            
            self.cam = coin.SoOrthographicCamera()
            self.cam.aspectRatio = 1
            self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE

            self.trans = coin.SoTranslation()
            self.trans.translation = (-0.95,0.95,0)

            self.myFont = coin.SoFont()
            self.myFont.name = "osiFont,FreeSans,sans"
            self.myFont.size.setValue(16.0)
            #self.trans = coin.SoTranslation()
            self.SoText2  = coin.SoText2()
            #self.trans.translation.setValue(.25,.0,1.25)
            self.SoText2.string = "" #"Nothing Selected\r2nd line"
            self.color = coin.SoBaseColor()
            self.color.rgb = (0,0,0)

            self.textSep.addChild(self.cam)
            self.textSep.addChild(self.trans)
            self.textSep.addChild(self.color)
            self.textSep.addChild(self.myFont)
            #self.textSep.addChild(self.trans)
            self.textSep.addChild(self.SoText2)
            #self.Active = False
            #self.sg.addChild(self.textSep)
            
            self.viewer=self.view.getViewer()
            self.render=self.viewer.getSoRenderManager()
            self.sup = self.render.addSuperimposition(self.textSep)
            self.sg.touch()
            #self.cam2 = coin.SoPerspectiveCamera()
            #self.sg.addChild(self.cam2)
            
            self.Active = True
            self.viz = False
            self.getTopo()
        elif (index == 0) and self.Active:
            print "GeomInfo off"
            self.render.removeSuperimposition(self.sup)
            if self.viz:
                self.root.removeChild(self.node)
                self.viz = False
            self.sg.touch()
            self.Active = False
        #else:
            #print "Else ....."
            #self.sg.addChild(self.textSep)

    def addSelection(self,doc,obj,sub,pnt):   # Selection
        if self.Active:
            self.getTopo()
    def removeSelection(self,doc,obj,sub):    # Effacer l'objet selectionne
        if self.Active:
            self.SoText2.string = ""
            if self.viz:
                self.root.removeChild(self.node)
                self.viz = False
    def setPreselection(self, doc, obj, sub):
        pass
    def clearSelection(self,doc):             # Si clic sur l'ecran, effacer la selection
        if self.Active:
            self.SoText2.string = ""
            if self.viz:
                self.root.removeChild(self.node)
                self.viz = False
    def getSurfInfo(self,surf):
        ret = []
        ret.append(beautify(str(surf)))
        try:
            ret.append("Poles  : " + str(surf.NbUPoles) + " x " + str(surf.NbVPoles))
            ret.append("Degree : " + str(surf.UDegree) + " x " + str(surf.VDegree))
            ret.append("Continuity : " + surf.Continuity)
            funct = [(surf.isURational,"U Rational"),
                    (surf.isVRational, "V Rational"),
                    (surf.isUPeriodic, "U Periodic"),
                    (surf.isVPeriodic, "V Periodic"),
                    (surf.isUClosed,   "U Closed"),
                    (surf.isVClosed,   "V Closed"),]
            for i in funct:
                if i[0]():
                    ret.append(i[1])
            funct = [(surf.getUKnots,"U Knots"),
                     (surf.getUMultiplicities,"U Mults"),
                     (surf.getVKnots,"V Knots"),
                     (surf.getVMultiplicities,"V Mults")]
            for i in funct:
                r = i[0]()
                if r:
                    s = str(i[1]) + " : " + str(r)
                    ret.append(s)
            #FreeCAD.Console.PrintMessage(ret)
            return ret
        except:
            return ret
        
    def getCurvInfo(self,curve):
        ret = []
        ret.append(beautify(str(curve)))
        try:
            ret.append("Poles  : " + str(curve.NbPoles))
            ret.append("Degree : " + str(curve.Degree))
            ret.append("Continuity : " + curve.Continuity)
            funct = [(curve.isRational,"Rational"),
                    (curve.isPeriodic, "Periodic"),
                    (curve.isClosed,   "Closed")]
            for i in funct:
                if i[0]():
                    ret.append(i[1])
            r = curve.getKnots()
            s = "Knots : " + str(removeDecim(r))
            ret.append(s)
            r = curve.getMultiplicities()
            s = "Mults : " + str(r)
            ret.append(s)
            return ret
        except:
            return ret

    def getTopo(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel != []:
            
            sel0 = sel[0]
            if sel0.HasSubObjects:
                ss = sel0.SubObjects[-1]
                if ss.ShapeType == 'Face':
                    #FreeCAD.Console.PrintMessage("Face detected"+ "\n")
                    surf = ss.Surface
                    t = self.getSurfInfo(surf)
                    self.SoText2.string.setValues(0,len(t),t)
                elif ss.ShapeType == 'Edge':
                    #FreeCAD.Console.PrintMessage("Edge detected"+ "\n")
                    cur = ss.Curve
                    t = self.getCurvInfo(cur)
                    self.SoText2.string.setValues(0,len(t),t)
                    if self.viz:
                        self.root.removeChild(self.node)
                        self.viz = False
                    self.root = sel0.Object.ViewObject.RootNode
                    self.node = curveNode(cur)
                    if self.node:
                        self.root.addChild(self.node)
                        self.viz = True

    def GetResources(self):
        #return {'Pixmap'  : 'python', 'MenuText': 'Toggle command', 'ToolTip': 'Example toggle command', 'Checkable': True}
        return {'Pixmap' : path_curvesWB_icons+'/info.svg', 'MenuText': 'Geometry Info', 'ToolTip': 'displays info about the geometry of the selected topology', 'Checkable': False}
FreeCADGui.addCommand('GeomInfo', GeomInfo())
