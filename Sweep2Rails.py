from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
import libS2R

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

fac = 1.0
DEBUG = False

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
        obj.Blending = "Average"
        obj.ProfileSamples = 20
        obj.RailSamples = 40
        obj.Parametrization = 0.0
        obj.Extend = False


    def execute(self, obj):
        if hasattr(obj,"Birail") and hasattr(obj,"Profiles"):
            if (not obj.Birail == None) and (not obj.Profiles == []):
                s2r = libS2R.SweepOn2Rails()
                s2r.parametrization = obj.Parametrization
                s2r.extend = obj.Extend
                s2r.profileSamples = obj.ProfileSamples
                s2r.railSamples = obj.RailSamples
                
                s2r.setRails(obj.Birail.Shape.Face1)
                s2r.setProfiles(self.setProfiles(obj.Profiles)) #((e1,e2,e3))
                s2r.build()
                #s2r.showLocalProfiles()
                #s2r.showInterpoCurves()
                s2r.mix(obj.Blending)
                #s2r.show()
                obj.Shape = s2r.shape()
                

    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage('%s changed\n'%prop)
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
            #n = len(fp.Profiles) - 1
            #gr = int(1.0 * fp.RailSamples / n) + 1
            #fp.RailSamples = gr * n
            
    def setProfiles(self, prop):
        a = []
        for obj in prop:
            a.append(obj.Shape.Edges[0])
        return(a)



class sweep2railsVP:
    def __init__(self, obj):
        obj.Proxy = self
        
    def getIcon(self):
        return (path_curvesWB_icons+'/sw2r.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    def claimChildren(self):
        a = self.Object.Profiles
        a.append(self.Object.Birail)
        return(a)
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        try:
            self.Object.Birail.ViewObject.show()
            for p in self.Object.Profiles:
                p.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True

class s2rCommand:
    def parseSel(self, selectionObject):
        birail = None
        profs = []
        for obj in selectionObject:
            if hasattr(obj,"NormalizeBinormal") or hasattr(obj,"Orientation"): #if isinstance(obj.Proxy, birail):
                birail = obj
            else:
                profs.append(obj)
        return((birail,profs))

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        if s == []:
            FreeCAD.Console.PrintError("Select a ruled surface and a list of profile edges\n")
            return
            
        myS2R = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Sweep 2 rails")
        sweep2rails(myS2R)
        sweep2railsVP(myS2R.ViewObject)

        myS2R.Birail   = self.parseSel(s)[0]
        myS2R.Profiles = self.parseSel(s)[1]
        myS2R.Birail.ViewObject.Visibility = False
        for p in myS2R.Profiles:
            p.ViewObject.Visibility = False

        myS2R.ViewObject.PointSize = 2.00000
        FreeCAD.ActiveDocument.recompute()


    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/sw2r.svg', 'MenuText': 'Sweep2Rails', 'ToolTip': 'Sweep profiles on 2 rails'}

FreeCADGui.addCommand('sw2r', s2rCommand())







