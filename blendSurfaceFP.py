from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
import blendSurface
import CoinNodes
from pivy import coin

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')


def downgradeArray(arr):
    pt1 = []
    for row in arr:
        pt1 += row
    return(pt1)

        
def shapeCloud(arr):
    v = []
    for row in arr:
        for pt in row:
            v.append(Part.Vertex(pt))
    c = Part.Compound(v)
    return(c)

class blendSurfFP:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink",       "Edge1",          "Base",   "First edge")
        obj.addProperty("App::PropertyLink",       "Edge2",          "Base",   "Second edge")
        #obj.addProperty("App::PropertyEnumeration","Blending",       "Base",   "Blending method").Blending = ["Average","Blend","Rail1","Rail2"]
        obj.addProperty("App::PropertyPlacement",  "Placement",      "Base",   "Placement")
        obj.addProperty("App::PropertyInteger",    "ProfileSamples", "BlendSurface",   "Profile Samples")
        obj.addProperty("App::PropertyInteger",    "RailSamples",    "BlendSurface",   "Edge Samples")
        obj.addProperty("App::PropertyBool",       "Untwist",        "BlendSurface",   "Untwist surface")
        obj.addProperty("App::PropertyVectorList", "Points",         "BlendSurface",   "Points")
        obj.addProperty("Part::PropertyPartShape", "Shape",          "BlendSurface",   "Shape")
        #obj.Blending = "Blend"
        obj.ProfileSamples = 20
        obj.RailSamples = 20
        #obj.Parametrization = 0.0
        obj.Untwist = False


    def execute(self, obj):
        if hasattr(obj,"Edge1") and hasattr(obj,"Edge2"):
            if (not obj.Edge1 == None) and (not obj.Edge2 == None):
                
                bs = blendSurface.blendSurface(obj.Edge1, obj.Edge2)
                bs.railSamples = obj.RailSamples
                bs.profSamples = obj.ProfileSamples
                bs.untwist = obj.Untwist
                
                bs.buildCurves()
                pts = bs.getPoints()
                
                obj.Points = downgradeArray(pts)
                obj.Shape = shapeCloud(pts)
                

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



class blendSurfVP:
    def __init__(self, obj):
        obj.Proxy = self
        #self.attach(obj)
        
    def getIcon(self):
        return (path_curvesWB_icons+'/blendSurf.svg')

    def attach(self, vobj):
        #self.ViewObject = vobj
        self.Object = vobj.Object
        
        self.gridDM = coin.SoGroup()
        self.pointsDM = coin.SoGroup()
        self.ProfDM = coin.SoGroup()
        self.railDM = coin.SoGroup()
        
        self.coord = CoinNodes.coordinate3Node(self.Object.Points)
        self.row = CoinNodes.rowNode((0.8,0.4,0.4),1.0)
        self.col = CoinNodes.colNode((0.4,0.4,0.8),1.0)
        self.pointSet = coin.SoPointSet()
        self.style = CoinNodes.styleNode((0,0,0),1.0,2.0)
        self.style.addChild(self.pointSet)
        
        #vobj.addChild(self.coord)
        
        self.ProfDM.addChild(self.coord)
        self.ProfDM.addChild(self.row)
        
        self.railDM.addChild(self.coord)
        self.railDM.addChild(self.col)
        
        self.gridDM.addChild(self.coord)
        self.gridDM.addChild(self.row)
        self.gridDM.addChild(self.col)

        self.pointsDM.addChild(self.coord)
        self.pointsDM.addChild(self.style)
        #self.points.addChild(self.pointSet)
        
        vobj.addDisplayMode(self.gridDM,"Wireframe")
        vobj.addDisplayMode(self.pointsDM,"Points")
        vobj.addDisplayMode(self.ProfDM,"Profiles")
        vobj.addDisplayMode(self.railDM,"Rails")
        #self.onChanged(vobj,"DisplayMode")
        #if "Wireframe" in vobj.listDisplayModes():
            #vobj.DisplayMode = "Wireframe"

    def updateData(self, fp, prop):
        FreeCAD.Console.PrintMessage("updateDate : " + str(prop) + "\n")
        if len(fp.Points) == fp.RailSamples * fp.ProfileSamples :
            self.coord.points = fp.Points
            self.row.vertices = (fp.RailSamples, fp.ProfileSamples)
            self.col.vertices = (fp.RailSamples, fp.ProfileSamples)
            colors1 = [(0.0,0.8,0.0)] * (fp.ProfileSamples - 1)
            colors2 = [(0.8,0.4,0.4)] * (fp.RailSamples - 2)* (fp.ProfileSamples-1)
            colors3 = [(0.8,0.8,0.0)] * (fp.ProfileSamples - 1)
            colors = colors1 + colors2 + colors3
            self.row.binding.value = coin.SoMaterialBinding.PER_PART
            self.row.coinColor.diffuseColor.setValues(0,len(colors),colors)

    def onChanged(self, vp, prop):
        "Here we can do something when a single property got changed"
        FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def getDisplayModes(self,obj):
         "Return a list of display modes."
         modes=[]
         modes.append("Points")
         modes.append("Profiles")
         modes.append("Rails")
         modes.append("Wireframe")
         return modes

    def getDefaultDisplayMode(self):
         "Return the name of the default display mode. It must be defined in getDisplayModes."
         return "Wireframe"

    def setDisplayMode(self,mode):
         return mode
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def claimChildren(self):
        a = [self.Object.Edge1, self.Object.Edge2]
        return(a)
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            self.Object.Edge1.ViewObject.show()
            self.Object.Edge2.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True

class blendSurfCommand:
    def parseSel(self, selectionObject):
        birail = None
        cos = []
        for obj in selectionObject:
            if hasattr(obj,"ReverseBinormal"): #obj is a curveOnSurface
                cos.append(obj)
        return(cos)

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s == []:
            FreeCAD.Console.PrintError("Select 2 CurveOnSurface objects.\n")
            return
            
        myblSu = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Blend_Surface")
        blendSurfFP(myblSu)
        blendSurfVP(myblSu.ViewObject)

        myblSu.Edge1 = self.parseSel(s)[0]
        myblSu.Edge2 = self.parseSel(s)[1]
        myblSu.Edge1.ViewObject.Visibility = False
        myblSu.Edge2.ViewObject.Visibility = False
        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/blendSurf.svg', 'MenuText': 'Blend Surface', 'ToolTip': 'Blending Surface between to curveOnSurface objects '}

FreeCADGui.addCommand('blendSurface', blendSurfCommand())







