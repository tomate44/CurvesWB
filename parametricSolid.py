import os
import FreeCAD, FreeCADGui, Part
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

def increaseContinuity(c,tol):
    #oc = c.Continuity
    mults = [int(m) for m in c.getMultiplicities()]
    #knots = c.getKnots()
    try:
        for i in range(len(mults))[1:-1]:
            rk = c.removeKnot(i+1,mults[i]-1,tol)
    except Part.OCCError:
        debug('failed to increase continuity.')
        debug("curve has %d poles."%len(c.getPoles()))
    return(c)    

def alignedTangents(c0, c1, Tol):
    t0 = c0.tangent(c0.LastParameter)[0]
    t1 = c1.tangent(c1.FirstParameter)[0]
    t0.normalize()
    t1.negative()
    t1.normalize()
    v = t0.sub(t1)
    if v.Length < Tol:
        return(True)
    else:
        return(False)
    


class solid:
    "Make a parametric solid from selected faces"
    def __init__(self, obj):
        ''' Add the properties ''' 
        obj.addProperty("App::PropertyLinkSubList",   "Faces",        "Solid",  "List of faces to build the solid")
        #obj.addProperty("App::PropertyLink",         "Base",         "Join",   "Join all the edges of this base object")
        #obj.addProperty("App::PropertyFloat",        "Tolerance",    "Join",   "Tolerance").Tolerance=0.001
        #obj.addProperty("App::PropertyBool",         "CornerBreak",  "Join",   "Break on corners").CornerBreak = False
        #obj.addProperty("App::PropertyBool",         "BadContinuity","Join",   "Break On Bad C0 Continuity").BadContinuity = False
        obj.Proxy = self

    def getFaces(self, obj):
        res = []
        if hasattr(obj, "Faces"):
            for l in obj.Faces:
                o = l[0]
                for ss in l[1]:
                    n = eval(ss.lstrip('Face'))
                    res.append(o.Shape.Faces[n-1])
        return(res)

    def execute(self, obj):
        faces = self.getFaces(obj)
        shell = Part.Shell(faces)
        obj.Shape = Part.Solid(shell)

class solidVP:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/solid.svg')

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

    #def claimChildren(self):
        #return None #[self.Object.Base, self.Object.Tool]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        return True


class solidCommand:
    "Make a parametric solid from selected faces"
    def makeSolidFeature(self,source):
        solidFP = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Solid")
        solid(solidFP)
        solidVP(solidFP.ViewObject)
        solidFP.Faces = source
        FreeCAD.ActiveDocument.recompute()
        #solidFP.ViewObject.LineWidth = 2.0
        #solidFP.ViewObject.LineColor = (0.3,0.5,0.5)

    def Activated(self):
        faces = []
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel == []:
            FreeCAD.Console.PrintError("Select some faces first !\n")
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Face):
                        faces.append((selobj.Object, selobj.SubElementNames[i]))
            elif selobj.Object.Shape.Faces:
                for i in range(len(selobj.Object.Shape.Faces)):
                    faces.append((selobj.Object, "Face%d"%i))
                selobj.Object.ViewObject.Visibility = False
        if faces:
            self.makeSolidFeature(faces)
        
    def IsActive(self):
        if FreeCAD.ActiveDocument:
            #f = FreeCADGui.Selection.Filter("SELECT Part::Feature SUBELEMENT Face COUNT 1..1000")
            #return f.match()
            return(True)
        else:
            return(False)

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/solid.svg', 'MenuText': 'Make Solid', 'ToolTip': 'Make a parametric solid from selected faces'}

FreeCADGui.addCommand('solid', solidCommand())
