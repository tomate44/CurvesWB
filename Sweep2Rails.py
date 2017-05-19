 
import FreeCAD
import FreeCADGui
import math
from pivy import coin

class sweep2rails:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink",       "Birail",        "Base",   "Birail object")
        obj.addProperty("App::PropertyLinkList",   "Profiles",      "Base",   "List of profiles")
        obj.addProperty("App::PropertyEnumeration","Blending",      "Base",   "Blending method").Blending = ["Average","Blend","Rail1","Rail2"]
        obj.addProperty("App::PropertyInteger",    "ProfileSamples","Base",   "Profile Samples")
        obj.addProperty("App::PropertyInteger",    "RailSamples",   "Base",   "Profile Samples")
        obj.Blending = "Blend"
        obj.ProfileSamples = 20
        obj.RailSamples = 20
        self.birail = None
        self.profiles = None

    def execute(self, obj):
        return()
        self.ruledSurface()
        obj.Shape = self.ruled

    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage('%s changed\n'%prop)
        if prop == "Birail":
            self.birail = fp.Birail
            self.setParams()
        if prop == "Profiles":
            self.setProfiles(fp.Profiles)
            self.setParams()
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
            
    def setProfiles(self, prop):
        a = []
        for obj in prop:
            a.append(obj.Shape.Edges[0])
        self.profiles = a

    def setParams(self):
        if self.birail and self.profiles:
            self.knots1, self.knots2 = [],[]
            for pro in self.profiles:
                sols1 = pro.distToShape(self.birail.Shape.Edges[0])[1][0]
                sols2 = pro.distToShape(self.birail.Shape.Edges[2])[1][0]
                FreeCAD.Console.PrintMessage("%s\n"%str(sols1))
                self.knots1.append(self.birail.Shape.Edges[0].Curve.parameter(sols1[1]))
                self.knots2.append(self.birail.Shape.Edges[2].Curve.parameter(sols2[1]))

class sweep2railsVP:
    def __init__(self, obj):
        obj.Proxy = self
        
    #def getIcon(self):
        #return (path_curvesWB_icons+'/isocurve.svg')

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
            App.Console.PrintError("Error in onDelete: " + err.message)
        return True

def parseSel(selectionObject):
    birail = None
    profs = []
    for obj in selectionObject:
        if hasattr(obj,"NormalizeBinormal"): #if isinstance(obj.Proxy, birail):
            birail = obj
        else:
            profs.append(obj)
    return((birail,profs))

myS2R = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Sweep 2 rails")
sweep2rails(myS2R)
sweep2railsVP(myS2R.ViewObject)

s = FreeCADGui.Selection.getSelection()
myS2R.Birail   = parseSel(s)[0]
myS2R.Profiles = parseSel(s)[1]
myS2R.Birail.ViewObject.Visibility = False
for p in myS2R.Profiles:
    p.ViewObject.Visibility = False


#g=FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup","Groupe")

#for m in mm:
    #out = []
    #for p in outpts:
        #out.append(m.multiply(p))
    #c = Part.Compound([Part.Vertex(pt) for pt in out])
    #o = FreeCAD.ActiveDocument.addObject("Part::Feature","pro")
    #o.Shape = c
    #g.addObject(o)





