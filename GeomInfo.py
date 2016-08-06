import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')



class GeomInfo:
    "this class displays info about the geometry of the selected topology"
    def Activated(self):
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.stack = []
        FreeCADGui.Selection.addObserver(self)    # installe la fonction en mode resident
        #FreeCADGui.Selection.addObserver(self.getTopo)
        self.active = True
        self.sg = self.view.getSceneGraph()
        self.textSep = coin.SoSeparator()
        self.myFont = coin.SoFont()
        #self.myFont.name.setValue("Times-Roman")
        self.myFont.size.setValue(12.0);
        #self.trans = coin.SoTranslation()
        self.SoText2  = coin.SoText2()
        #self.trans.translation.setValue(.25,.0,1.25)
        self.SoText2.string = "" #"Nothing Selected\r2nd line"
        self.textSep.addChild(self.myFont)
        #self.textSep.addChild(self.trans)
        self.textSep.addChild(self.SoText2)
        self.sg.addChild(self.textSep)

    def addSelection(self,doc,obj,sub,pnt):   # Selection
        self.getTopo()
    def removeSelection(self,doc,obj,sub):    # Effacer l'objet salectionne
        self.SoText2.string = ""
    def setPreselection(self, doc, obj, sub):
        pass
    def clearSelection(self,doc):             # Si clic sur l'ecran, effacer la selection
        self.SoText2.string = ""

    def getSurfInfo(self,surf):
        ret = ""
        ret += str(surf) + "\n"
        ret += "Poles  : " + str(surf.NbUPoles) + " x " + str(surf.NbVPoles) + "\n"
        ret += "Degree : " + str(surf.UDegree) + " x " + str(surf.VDegree) + "\n"
        FreeCAD.Console.PrintMessage(ret)
        return ret
        
    def getCurvInfo(self,edge):
        ret = ""
        ret += str(edge) + "\n"
        FreeCAD.Console.PrintMessage(ret)
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
                    self.SoText2.string = self.getSurfInfo(surf)
                elif ss.ShapeType == 'Edge':
                    FreeCAD.Console.PrintMessage("Edge detected"+ "\n")
                    edge = ss.Curve
                    self.SoText2.string = self.getCurvInfo(edge)

    def GetResources(self):
            return {'Pixmap' : path_curvesWB_icons+'/info.svg', 'MenuText': 'Geometry Info', 'ToolTip': 'displays info about the geometry of the selected topology'}
FreeCADGui.addCommand('GeomInfo', GeomInfo())
