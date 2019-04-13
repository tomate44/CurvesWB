import sys
if sys.version_info.major >= 3:
    from importlib import reload
import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import dummy
import isocurves
import CoinNodes as coinNodes
reload(coinNodes)


path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

def beautify(shp):
    if not shp:
        return("")
    else:
        t = shp
        if (shp[0] == "<") and (shp[-1] == ">"):
            t = shp[1:-1]
        return(t.split()[0])

def getString(weights):
    weightStr = []
    for w in weights:
        if abs(w-1.0) < 0.001:
            weightStr.append("")
        elif w.is_integer():
            weightStr.append(" %d"%int(w))
        else:
            weightStr.append(" %0.2f"%w)
    return(weightStr)

def cleanString(arr):
    strArr = ""
    for w in arr:
        if isinstance(w,float):
            strArr += "%0.2f, "%w
        else:
            strArr += "%d, "%int(w)
    return(strArr[:-2])

def coordStr(v):
    if hasattr(v,'x'):
        s = "%0.2f"%v.x
        if hasattr(v,'y'):
            s += ", %0.2f"%v.y
            if hasattr(v,'z'):
                s += ", %0.2f"%v.z
        return(s)
    else:
        return(v)

def removeDecim(arr):
    r = []
    for fl in arr:
        r.append("%0.2f"%fl)
    return r

def to1D(arr):
    array = []
    for row in arr:
        for el in row:
            array.append(el)
    return array

def paramList(n, fp, lp):
    rang = lp-fp
    l = []
    if n == 1:
        l = [fp + rang / 2.0]
    elif n == 2:
        l = [fp,lp]
    elif n > 2:
        for i in range(n):
            l.append( fp + 1.0* i* rang / (n-1) )
    return(l)

def curveNode(cur):
    bspline = False
    rational = False
    try:
        poles = cur.getPoles()
        weights = cur.getWeights()
    except:
        return False
    try:
        rational = cur.isRational()
    except:
        pass
    try:
        knots = cur.getKnots()
        mults = cur.getMultiplicities()
        bspline = True
    except:
        bspline = False


    # *** Set poles ***    
    polesnode = coinNodes.coordinate3Node(poles)

    # *** Set weights ***    
    weightStr = getString(weights)

    polySep = coinNodes.polygonNode((0.5,0.5,0.5),1)
    polySep.vertices = poles

    # *** Set markers ***    
    markerSep = coinNodes.markerSetNode((1,0,0),coin.SoMarkerSet.DIAMOND_FILLED_9_9)
    markerSep.color = [(1,0,0)]+[(0.5,0.0,0.5)]*(len(poles)-1)

    if rational:
        # *** Set weight text ***
        weightSep = coinNodes.multiTextNode((1,0,0),"osiFont,FreeSans,sans",16,0)
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
            multStr.append("\n%d"%m)
        
        knotMarkerSep = coinNodes.markerSetNode((0,0,1),coin.SoMarkerSet.CIRCLE_FILLED_5_5)
        knotMarkerSep.color = [(0,0,1)]*len(knotPoints)

        # *** Set mult text ***        
        multSep = coinNodes.multiTextNode((0,0,1),"osiFont,FreeSans,sans",16,1)
        multSep.data = (knotPoints,multStr)

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
    except:
        return False
    try:
        rational = surf.isURational() or surf.isVRational()
    except:
        pass
    try:
        uknots = surf.getUKnots()
        umults = surf.getUMultiplicities()
        vknots = surf.getVKnots()
        vmults = surf.getVMultiplicities()
        bspline = True
    except:
        bspline = False


    # *** Set poles ***    
    flatPoles = to1D(poles)
    polesnode = coinNodes.coordinate3Node(flatPoles)

    # *** Set weights ***    
    flatW = to1D(weights)
    weightStr = getString(flatW)

    polyRowSep = coinNodes.rowNode((0.5,0,0),1)
    polyRowSep.vertices=(nbU,nbV)
    polyRowSep.color = [(0.5,0.0,0.0)]*len(flatPoles)
    polyColSep = coinNodes.colNode((0,0,0.5),1)
    polyColSep.vertices=(nbU,nbV)
    polyColSep.color = [(0.0,0.0,0.5)]*len(flatPoles)

    # *** Set markers ***    
    markerSep = coinNodes.markerSetNode((1,0,0),coin.SoMarkerSet.DIAMOND_FILLED_9_9)
    markerSep.color = [(1,0,0)]+[(0.5,0.0,0.5)]*(len(flatPoles)-1)

    u0,u1,v0,v1 = surf.bounds()
    halfU = u0 + 1.*(u1-u0)/2
    halfV = v0 + 1.*(v1-v0)/2
    UPos = surf.value(halfU,v0)
    Uletter = coinNodes.text2dNode((0,0,0),"osiFont,FreeSans,sans",20,(UPos.x,UPos.y,UPos.z),'U')
    VPos = surf.value(u0,halfV)
    Vletter = coinNodes.text2dNode((0,0,0),"osiFont,FreeSans,sans",20,(VPos.x,VPos.y,VPos.z),'V')

    vizSep = coin.SoSeparator()
    vizSep.addChild(polesnode)
    vizSep.addChild(polyRowSep)
    vizSep.addChild(polyColSep)
    vizSep.addChild(markerSep)
    vizSep.addChild(Uletter)
    vizSep.addChild(Vletter)
    if rational:
        # *** Set weight text ***
        weightSep = coinNodes.multiTextNode((1,0,0),"osiFont,FreeSans,sans",16,0)
        weightSep.data = (flatPoles,weightStr)
        vizSep.addChild(weightSep)

    if bspline:

        # *** Set knots ***
        uknotPoints = []
        nb_curves = 0
        for k in uknots:
            try:
                uIso = surf.uIso(k)
                epts = uIso.toShape().discretize(100)
                if len(epts) == 100:
                    for p in epts:
                        uknotPoints.append((p.x,p.y,p.z))
                    nb_curves += 1
            except:
                FreeCAD.Console.PrintError("Error computing surface U Iso\n")
            
        if nb_curves > 0:
            uknotsnode = coinNodes.coordinate3Node(uknotPoints)
            uCurves = coinNodes.rowNode((1.0,0.5,0.3),3)
            uCurves.color = [(1.0,0.5,0.3)]*99
            uCurves.color += [(0.7,0.0,0.3)]*(nb_curves-1)*99
            uCurves.vertices=(nb_curves,100)
            vizSep.addChild(uknotsnode)
            vizSep.addChild(uCurves)
            #debug(str(uCurves.vertices))
        
        vknotPoints = []
        nb_curves = 0
        for k in vknots:
            try:
                vIso = surf.vIso(k)
                epts = vIso.toShape().discretize(100)
                if len(epts) == 100:
                    for p in epts:
                        vknotPoints.append((p.x,p.y,p.z))
                    nb_curves += 1
            except:
                FreeCAD.Console.PrintError("Error computing surface V Iso\n")
        
        
        if nb_curves > 0:
            vknotsnode = coinNodes.coordinate3Node(vknotPoints)
            vCurves = coinNodes.rowNode((0.3,0.5,1.0),3)
            vCurves.color = [(0.8,0.8,0.0)]*99
            vCurves.color += [(0.3,0.0,0.7)]*(nb_curves-1)*99
            vCurves.vertices=(nb_curves,100)
            vizSep.addChild(vknotsnode)
            vizSep.addChild(vCurves)

        # removed because of several FC crashes
        ## ***** isoCurves ******
        
        #uparam = paramList(16,u0,u1)
        #uisoPoints = []
        #nb_curves = 0
        #for k in uparam:
            #try:
                #uIso = surf.uIso(k)
                #epts = uIso.toShape().discretize(100)
                #if len(epts) == 100:
                    #for p in epts:
                        #uisoPoints.append((p.x,p.y,p.z))
                    #nb_curves += 1
            #except:
                #FreeCAD.Console.PrintError("Error computing surface U Iso\n")
        
        #if nb_curves > 0:
            #uisonode = coinNodes.coordinate3Node(uisoPoints)
            #uisoCurves = coinNodes.rowNode((0.0,0.0,0.0),1)
            #uisoCurves.transparency = 0.8
            #uisoCurves.vertices=(nb_curves,100)
            #vizSep.addChild(uisonode)
            #vizSep.addChild(uisoCurves)
            ##debug(str(uCurves.vertices))
        
        #vparam = paramList(16,v0,v1)
        #visoPoints = []
        #nb_curves = 0
        #for k in vparam:
            #try:
                #vIso = surf.vIso(k)
                #epts = vIso.toShape().discretize(100)
                #if len(epts) == 100:
                    #for p in epts:
                        #vknotPoints.append((p.x,p.y,p.z))
                    #nb_curves += 1
            #except:
                #FreeCAD.Console.PrintError("Error computing surface V Iso\n")
        
        #if nb_curves > 0:
            #visonode = coinNodes.coordinate3Node(visoPoints)
            #visoCurves = coinNodes.rowNode((0.0,0.0,0.0),1)
            #visoCurves.transparency = 0.8
            #visoCurves.vertices=(nb_curves,100)
            #vizSep.addChild(visonode)
            #vizSep.addChild(visoCurves)

        ## *** Set texts ***        
        #multStr = []
        #for m in mults:
            #multStr.append("%d"%m)
        
        #knotMarkerSep = coinNodes.markerSetNode((0,0,1),coin.SoMarkerSet.CIRCLE_FILLED_9_9)

        ## *** Set mult text ***        
        #multSep = coinNodes.multiTextNode((0,0,1),"osiFont,FreeSans,sans",16,1)
        #multSep.data = (knotPoints,multStr)

    return(vizSep)


class GeomInfo:
    "this class displays info about the geometry of the selected shape"
    def Activated(self,index=0):

        if index == 1:
            debug("GeomInfo activated")
            #self.activeDoc = FreeCADGui.ActiveDocument
            #self.view = self.activeDoc.ActiveView
            self.stack = []
            FreeCADGui.Selection.addObserver(self)    # installe la fonction en mode resident
            #FreeCADGui.Selection.addObserver(self.getTopo)
            self.active = True
            #self.sg = self.view.getSceneGraph()
            self.textSep = coin.SoSeparator()
            
            self.cam = coin.SoOrthographicCamera()
            self.cam.aspectRatio = 1
            self.cam.viewportMapping = coin.SoCamera.LEAVE_ALONE

            self.trans = coin.SoTranslation()
            self.trans.translation = (-0.98,0.90,0)

            self.myFont = coin.SoFont()
            self.myFont.name = "FreeMono,FreeSans,sans"
            self.myFont.size.setValue(14.0)
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
            
            #self.viewer=self.view.getViewer()
            #self.render=self.viewer.getSoRenderManager()
            #self.sup = self.render.addSuperimposition(self.textSep)
            #self.sg.touch()
            #self.cam2 = coin.SoPerspectiveCamera()
            #self.sg.addChild(self.cam2)
            
            #self.sensor = coin.SoFieldSensor(self.updateCB, None)
            #self.sensor.setData(self.sensor)
            #self.sensor.setPriority(0)
            
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
        self.activeDoc = FreeCADGui.ActiveDocument
        self.view = self.activeDoc.ActiveView
        self.sg = self.view.getSceneGraph()
        self.viewer=self.view.getViewer()
        self.render=self.viewer.getSoRenderManager()
        self.sup = self.render.addSuperimposition(self.textSep)
        self.sg.touch()

    def removeHUD(self):
        if self.render:
            self.render.removeSuperimposition(self.sup)
            self.removeGrid()
            self.sg.touch()

    #def updateCB(self, *args):
        ##return(True)
        #self.getTopo()

    def removeGrid(self):
        if self.viz:
            #self.root.removeChild(self.trans)
            self.root.removeChild(self.node)
            self.viz = False
            #self.sensor.detach()
    def insertGrid(self):
        if self.node:
            #self.trans = coin.SoMatrixTransform()
            #mat = self.placement.toMatrix()
            #self.trans.matrix.setValue(mat.A11, mat.A12, mat.A13, mat.A14, 
                                       #mat.A21, mat.A22, mat.A23, mat.A24, 
                                       #mat.A31, mat.A32, mat.A33, mat.A34, 
                                       #mat.A41, mat.A42, mat.A43, mat.A44 )
            #self.trans.matrix.setValue(mat.A11, mat.A21, mat.A31, mat.A41, 
                                       #mat.A12, mat.A22, mat.A32, mat.A42, 
                                       #mat.A13, mat.A23, mat.A33, mat.A43, 
                                       #mat.A14, mat.A24, mat.A34, mat.A44 )
            #self.root.addChild(self.trans)
            self.root.addChild(self.node)
            self.viz = True
            #self.sensor.attach(self.root)

# ------ Selection Observer --------

    def addSelection(self,doc,obj,sub,pnt):   # Selection
        FreeCAD.Console.PrintMessage("addSelection %s %s\n"%(obj,str(sub)))
        if self.Active:
            if not doc == self.activeDoc:
                self.removeHUD()
                self.addHUD()                
            self.getTopo()
    def removeSelection(self,doc,obj,sub):    # Effacer l'objet selectionne
        FreeCAD.Console.PrintMessage("removeSelection %s %s\n"%(obj,str(sub)))
        if self.Active:
            self.SoText2.string = ""
            self.removeGrid()
    def setPreselection(self, doc, obj, sub):
        pass
    def clearSelection(self,doc):             # Si clic sur l'ecran, effacer la selection
        FreeCAD.Console.PrintMessage("clearSelection\n")
        if self.Active:
            self.SoText2.string = ""
            self.removeGrid()

# ------ get info about shape --------


    def propStr(self,c,att):
        if hasattr(c,att):
            a = c.__getattribute__(att)
            if not a:
                return(False)
            elif hasattr(a,'x') and hasattr(a,'y') and hasattr(a,'z'):
                return("%s : (%0.2f, %0.2f, %0.2f)"%(att,a.x,a.y,a.z))
            else:
                return("%s : %s"%(att,str(a)))
        else:
            return(False)

    def propMeth(self,c,att):
        if hasattr(c,att):
            a = c.__getattribute__(att)()
            if not a:
                return(False)
            elif hasattr(a,'x') and hasattr(a,'y') and hasattr(a,'z'):
                return("%s : (%0.2f, %0.2f, %0.2f)"%(att,a.x,a.y,a.z))
            else:
                return("%s : %s"%(att,str(a)))
        else:
            return(False)

    def getSurfInfo(self,surf):
        ret = []
        ret.append(beautify(str(surf)))
        props = ['Center','Axis','Position','Radius','Direction','Location','Continuity']
        for p in props:
            s = self.propStr(surf,p)
            if s:
                ret.append(s)
        if isinstance(surf, (Part.BSplineSurface, Part.BezierSurface)):
            ret.append("Degree : %d x %d"%(surf.UDegree, surf.VDegree))
            ret.append("Poles  : %d x %d (%d)"%(surf.NbUPoles, surf.NbVPoles, surf.NbUPoles * surf.NbVPoles))
        props = ['isURational', 'isVRational', 'isUPeriodic', 'isVPeriodic', 'isUClosed', 'isVClosed']
        for p in props:
            s = self.propMeth(surf,p)
            if s:
                ret.append(s)
        if isinstance(surf, Part.BSplineSurface):
            funct = [(surf.getUKnots,"U Knots"),
                    (surf.getUMultiplicities,"U Mults"),
                    (surf.getVKnots,"V Knots"),
                    (surf.getVMultiplicities,"V Mults")]
            for i in funct:
                r = i[0]()
                if r:
                    s = str(i[1]) + " : " + cleanString(r)
                    ret.append(s)
        return(ret)
        
    def getCurvInfo(self,curve):
        ret = []
        ret.append(beautify(str(curve)))
        props = ['Center','Axis','Position','Radius','Direction','Location','Degree', 'NbPoles', 'Continuity']
        for p in props:
            s = self.propStr(curve,p)
            if s:
                ret.append(s)
        props = ['isRational', 'isPeriodic', 'isClosed']
        for p in props:
            s = self.propMeth(curve,p)
            if s:
                ret.append(s)
        if hasattr(curve,'getKnots'):
            r = curve.getKnots()
            s = "Knots : " + cleanString(r)
            ret.append(s)
        if hasattr(curve,'getMultiplicities'):
            r = curve.getMultiplicities()
            s = "Mults : " + cleanString(r)
            ret.append(s)
        if hasattr(curve,'length'):
            r = curve.length()
            if r < 1e80:
                s = "Length : " + cleanString([r])
                ret.append(s)
            else:
                ret.append("Length : Infinite")
        return(ret)

    def getTopo(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel != []:
            
            sel0 = sel[0]
            if sel0.HasSubObjects:
                try:
                    self.ss = sel0.SubObjects[-1]
                    self.so = sel0.Object
                except:
                    return
            else:
                return
            if self.ss.ShapeType == 'Face':
                #FreeCAD.Console.PrintMessage("Face detected"+ "\n")
                surf = self.ss.Surface
                t = self.getSurfInfo(surf)
                self.SoText2.string.setValues(0,len(t),t)
                self.removeGrid()
                #self.root = self.so.ViewObject.RootNode
                self.root = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
                #self.coord = self.root.getChild(1)
                self.node = surfNode(surf)
                #self.placement = self.ss.Placement
                self.insertGrid()
                #self.sensor.detach()
                #self.sensor.attach(self.coord.point)
            elif self.ss.ShapeType == 'Edge':
                #FreeCAD.Console.PrintMessage("Edge detected"+ "\n")
                cur = self.ss.Curve
                t = self.getCurvInfo(cur)
                self.SoText2.string.setValues(0,len(t),t)
                self.removeGrid()
                #self.root = self.so.ViewObject.RootNode
                self.root = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
                #self.coord = self.root.getChild(1)
                self.node = curveNode(cur)
                #self.placement = self.ss.Placement
                self.insertGrid()
                #self.sensor.detach()
                #self.sensor.attach(self.coord.point)

    def GetResources(self):
        #return {'Pixmap'  : 'python', 'MenuText': 'Toggle command', 'ToolTip': 'Example toggle command', 'Checkable': True}
        return {'Pixmap' : path_curvesWB_icons+'/info.svg', 'MenuText': 'Geometry Info', 'ToolTip': 'displays info about the geometry of the selected topology', 'Checkable': False}
FreeCADGui.addCommand('GeomInfo', GeomInfo())
