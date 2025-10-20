# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import FreeCAD
import FreeCADGui
import Part
from FreeCAD import Base
from freecad.Curves import blendSurface
from freecad.Curves import property_editor
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join( ICONPATH, 'blendSurf.svg')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


def downgradeArray(arr):
    pt1 = []
    for row in arr:
        pt1 += row
    return pt1

        
def shapeCloud(arr):
    v = []
    for row in arr:
        for pt in row:
            v.append(Part.Vertex(pt))
    c = Part.Compound(v)
    return c

def getComboView(mw):
    #from PySide.QtCore import * 
    dw=mw.findChildren(QDockWidget)
    for i in dw:
        if str(i.objectName()) == "Combo View":
            return i.findChild(QTabWidget)
        elif str(i.objectName()) == "Python Console":
            return i.findChild(QTabWidget)
    raise Exception ("No tab widget found")


class blendSurfFP:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink",       "Edge1",          "Base",   "First edge")
        obj.addProperty("App::PropertyLink",       "Edge2",          "Base",   "Second edge")
        #obj.addProperty("App::PropertyEnumeration","Blending",       "Base",   "Blending method").Blending = ["Average","Blend","Rail1","Rail2"]
        obj.addProperty("App::PropertyPlacement",  "Placement",      "Base",   "Placement")
        obj.addProperty("App::PropertyFloatConstraint", "Scale1",     "Edge1", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration",     "Continuity1","Edge1", "Continuity").Continuity1=["C0","G1","G2","G3","G4"]
        obj.addProperty("App::PropertyFloatConstraint", "Scale2",     "Edge2", "Scale of blend curve")
        obj.addProperty("App::PropertyEnumeration",     "Continuity2","Edge2", "Continuity").Continuity2=["C0","G1","G2","G3","G4"]
        obj.addProperty("App::PropertyInteger",    "ProfileSamples", "BlendSurface",   "Profile Samples")
        obj.addProperty("App::PropertyInteger",    "RailSamples",    "BlendSurface",   "Edge Samples")
        obj.addProperty("App::PropertyBool",       "Untwist",        "BlendSurface",   "Untwist surface")
        obj.addProperty("App::PropertyVectorList", "Points",         "BlendSurface",   "Points")
        obj.addProperty("App::PropertyVectorList", "ScaleList1",     "BlendSurface",   "Variable scale 1: list of vectors(parameter, scale1, 0)")
        obj.addProperty("App::PropertyVectorList", "ScaleList2",     "BlendSurface",   "Variable scale 2: list of vectors(parameter, scale2, 0)")

        obj.Continuity1 = "G2"
        obj.Continuity2 = "G2"
        obj.ProfileSamples = 20
        obj.RailSamples = 20
        obj.Scale1 = (1.,-5.0,5.0,0.05)
        obj.Scale2 = (1.,-5.0,5.0,0.05)
        #obj.ScaleList1 = ((0,1,0),(1,1,0))
        #obj.ScaleList2 = ((0,1,0),(1,1,0))
        obj.Untwist = False

    def check_scale_list(self, obj, prop):
        # TODO make the validation more strict
        valid = False
        if hasattr(obj,prop):
            if len(obj.getPropertyByName(prop)) > 0:
                valid = True
        return valid

    def execute(self, obj):
        if hasattr(obj,"Edge1") and hasattr(obj,"Edge2"):
            if (not obj.Edge1 is None) and (not obj.Edge2 is None):
                
                bs = blendSurface.blendSurface(obj.Edge1, obj.Edge2)
                bs.railSamples = obj.RailSamples
                bs.profSamples = obj.ProfileSamples
                if "Untwist" in obj.PropertiesList:
                    bs.untwist = obj.Untwist
                bs.cont1 = self.getContinuity(obj.Continuity1)
                bs.scale1 = obj.Scale1
                bs.cont2 = self.getContinuity(obj.Continuity2)
                bs.scale2 = obj.Scale2
                if self.check_scale_list(obj, "ScaleList1"):
                    bs.var_scale1 = obj.ScaleList1
                if self.check_scale_list(obj, "ScaleList2"):
                    bs.var_scale2 = obj.ScaleList2
                bs.buildCurves()
                #pts = bs.getPoints()
                
                #obj.Points = downgradeArray(pts)
                obj.Shape = bs.get_gordon_shapes() #shapeCloud(pts)
                return bs

    def getContinuity(self, cont):
        if cont == "C0":
            return 0
        elif cont == "G1":
            return 1
        elif cont == "G2":
            return 2
        elif cont == "G3":
            return 3
        else:
            return 4

    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage('%s changed\n'%prop)
        if prop == "Edge1":
            pass
        if prop == "Edge2":
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
        if prop == "Scale1":
            if fp.Scale1 == 0:
                fp.Scale1 = 0.0001
            self.execute(fp)
        elif prop == "Scale2":
            if fp.Scale2 == 0:
                fp.Scale2 = 0.0001
            self.execute(fp)


class blendSurfVP:
    def __init__(self, obj):
        obj.Proxy = self
        #self.attach(obj)
        
    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        #self.ViewObject = vobj
        self.Object = vobj.Object
        
        #self.gridDM = coin.SoGroup()
        #self.pointsDM = coin.SoGroup()
        #self.ProfDM = coin.SoGroup()
        #self.railDM = coin.SoGroup()
        
        #self.coord = CoinNodes.coordinate3Node(self.Object.Points)
        #self.row = CoinNodes.rowNode((0.8,0.4,0.4),1.0)
        #self.col = CoinNodes.colNode((0.4,0.4,0.8),1.0)
        #self.pointSet = coin.SoPointSet()
        #self.style = CoinNodes.styleNode((0,0,0),1.0,2.0)
        #self.style.addChild(self.pointSet)
        
        ##vobj.addChild(self.coord)
        
        #self.ProfDM.addChild(self.coord)
        #self.ProfDM.addChild(self.row)
        
        #self.railDM.addChild(self.coord)
        #self.railDM.addChild(self.col)
        
        #self.gridDM.addChild(self.coord)
        #self.gridDM.addChild(self.row)
        #self.gridDM.addChild(self.col)

        #self.pointsDM.addChild(self.coord)
        #self.pointsDM.addChild(self.style)
        ##self.points.addChild(self.pointSet)
        
        #vobj.addDisplayMode(self.gridDM,"Wireframe")
        #vobj.addDisplayMode(self.pointsDM,"Points")
        #vobj.addDisplayMode(self.ProfDM,"Profiles")
        #vobj.addDisplayMode(self.railDM,"Rails")
        ##self.onChanged(vobj,"DisplayMode")
        ##if "Wireframe" in vobj.listDisplayModes():
            ##vobj.DisplayMode = "Wireframe"

    #def updateData(self, fp, prop):
        #FreeCAD.Console.PrintMessage("updateDate : " + str(prop) + "\n")
        #if len(fp.Points) == fp.RailSamples * fp.ProfileSamples :
            #self.coord.points = fp.Points
            #self.row.vertices = (fp.RailSamples, fp.ProfileSamples)
            #self.col.vertices = (fp.RailSamples, fp.ProfileSamples)
            #colors1 = [(0.0,0.8,0.0)] * (fp.ProfileSamples - 1)
            #colors2 = [(0.8,0.4,0.4)] * (fp.RailSamples - 2)* (fp.ProfileSamples-1)
            #colors3 = [(0.8,0.8,0.0)] * (fp.ProfileSamples - 1)
            #colors = colors1 + colors2 + colors3
            #self.row.binding.value = coin.SoMaterialBinding.PER_PART
            #self.row.coinColor.diffuseColor.setValues(0,len(colors),colors)

    #def onChanged(self, vp, prop):
        #"Here we can do something when a single property got changed"
        #FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    #def getDisplayModes(self,obj):
         #"Return a list of display modes."
         #modes=[]
         #modes.append("Points")
         #modes.append("Profiles")
         #modes.append("Rails")
         #modes.append("Wireframe")
         #return modes

    #def getDefaultDisplayMode(self):
         #"Return the name of the default display mode. It must be defined in getDisplayModes."
         #return "Wireframe"

    #def setDisplayMode(self,mode):
         #return mode
  
    def setEdit(self,vobj,mode=0):
        if mode == 0:
            debug("Start Edit")
            self.ed = property_editor.VPEditor()
            self.group1 = self.ed.add_layout("Face 1")
            proped_11 = property_editor.VectorListWidget(self.Object,"ScaleList1")
            #proped_12 = property_editor.VectorListWidget() #self.Object,"Continuity1")
            #proped_11.fillTable(((0.0,1.0),(0.4,1.5),(1.0,0.8)))
            #proped_12.fillTable()
            self.ed.add_propeditor(proped_11, self.group1)
            #ed.add_propeditor(proped_12, self.group1)
            self.group2 = self.ed.add_layout("Face 2")
            proped_21 = property_editor.VectorListWidget(self.Object,"ScaleList2")
            #proped_22 = VectorListWidget() #self.Object,"Continuity2")
            self.ed.add_propeditor(proped_21, self.group2)
            #ed.add_propeditor(proped_22, self.group2)
            self.ed.add_close_button()

            self.mw = FreeCADGui.getMainWindow()
            self.ed.comboview = property_editor.getComboView(self.mw)
            self.ed.tabIndex = self.ed.comboview.addTab(self.ed.widget,"Table")
            self.ed.comboview.setCurrentIndex(self.ed.tabIndex)
            self.ed.widget.show()
            return True
        return False

    def unsetEdit(self,vobj,mode=0):
        debug("End Edit")
        FreeCADGui.ActiveDocument.resetEdit()
        if isinstance(self.ed,property_editor.VPEditor):
            self.ed.quit()
            self.ed = None
        self.Object.recompute()
        return False

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

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
        a = [self.Object.Edge1, self.Object.Edge2]
        return a
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            self.Object.Edge1.ViewObject.show()
            self.Object.Edge2.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: {0} \n".format(err))
        return True

class blendSurfCommand:
    def parseSel(self, selectionObject):
        birail = None
        cos = []
        for obj in selectionObject:
            if hasattr(obj,"ReverseBinormal"): #obj is a curveOnSurface
                cos.append(obj)
        return cos

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s == []:
            FreeCAD.Console.PrintError("Select 2 CurveOnSurface objects.\n")
            return
            
        myblSu = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Blend_Surface")
        blendSurfFP(myblSu)
        blendSurfVP(myblSu.ViewObject)

        myblSu.Edge1 = self.parseSel(s)[0]
        myblSu.Edge2 = self.parseSel(s)[1]
        myblSu.Edge1.ViewObject.Visibility = False
        myblSu.Edge2.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': 'Blend Surface',
                'ToolTip': 'Blend surface between two curveOnSurface objects'}

FreeCADGui.addCommand('blendSurface', blendSurfCommand())







