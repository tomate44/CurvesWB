import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import dummy

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

class GeomInfo:
    "this class displays info about the geometry of the selected topology"
    def Activated(self,index=0):

        if index == 1:
            print "Toggle is on"
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
            self.myFont.name = "Arial"
            self.myFont.size.setValue(10.0)
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
            self.getTopo()
        elif (index == 0) and self.Active:
            print "Toggle is off"
            self.render.removeSuperimposition(self.sup)
            self.sg.touch()
            self.Active = False
        #else:
            #print "Else ....."
            #self.sg.addChild(self.textSep)

    def addSelection(self,doc,obj,sub,pnt):   # Selection
        if self.Active:
            self.getTopo()
    def removeSelection(self,doc,obj,sub):    # Effacer l'objet salectionne
        if self.Active:
            self.SoText2.string = ""
    def setPreselection(self, doc, obj, sub):
        pass
    def clearSelection(self,doc):             # Si clic sur l'ecran, effacer la selection
        if self.Active:
            self.SoText2.string = ""

    def getSurfInfo(self,surf):
        ret = []
        ret.append(beautify(str(surf)))
        try:
            ret.append("Poles  : " + str(surf.NbUPoles) + " x " + str(surf.NbVPoles))
            ret.append("Degree : " + str(surf.UDegree) + " x " + str(surf.VDegree))
            funct = [(surf.isURational,"U Rational"),
                    (surf.isVRational,"V Rational"),
                    (surf.isUPeriodic,"U Periodic"),
                    (surf.isVPeriodic,"V Periodic"),
                    (surf.isUClosed,  "U Closed"),
                    (surf.isVClosed,  "V Closed"),]
            for i in funct:
                if i[0]():
                    ret.append(i[1])
            #FreeCAD.Console.PrintMessage(ret)
            return ret
        except:
            return ret
        
    def getCurvInfo(self,edge):
        ret = []
        ret.append(beautify(str(edge)))
        ret.append("Poles  : " + str(edge.NbPoles))
        ret.append("Degree : " + str(edge.Degree))
        #FreeCAD.Console.PrintMessage(ret)
        return ret

    def getTopo(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel != []:
            
            sel0 = sel[0]
            if sel0.HasSubObjects:
                ss = sel0.SubObjects[-1]
                if ss.ShapeType == 'Face':
                    FreeCAD.Console.PrintMessage("Face detected"+ "\n")
                    surf = ss.Surface
                    t = self.getSurfInfo(surf)
                    self.SoText2.string.setValues(0,len(t),t)
                elif ss.ShapeType == 'Edge':
                    FreeCAD.Console.PrintMessage("Edge detected"+ "\n")
                    edge = ss.Curve
                    t = self.getCurvInfo(edge)
                    self.SoText2.string.setValues(0,len(t),t)

    def GetResources(self):
        #return {'Pixmap'  : 'python', 'MenuText': 'Toggle command', 'ToolTip': 'Example toggle command', 'Checkable': True}
        return {'Pixmap' : path_curvesWB_icons+'/info.svg', 'MenuText': 'Geometry Info', 'ToolTip': 'displays info about the geometry of the selected topology', 'Checkable': False}
FreeCADGui.addCommand('GeomInfo', GeomInfo())
