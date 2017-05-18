import FreeCAD
import FreeCADGui
import math
from pivy import coin

class birail:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLinkSub",  "Edge1",   "Base",   "Edge1")
        obj.addProperty("App::PropertyLinkSub",  "Edge2",   "Base",   "Edge2")
        self.edge1 = None
        self.edge2 = None
    def execute(self, obj):
        return()
    def onChanged(self, fp, prop):
        FreeCAD.Console.PrintMessage('%s changed\n'%prop)
    def ruledSurface(self):
        if isinstance(self.edge1,Part.Edge) and isinstance(self.edge2,Part.Edge):
            self.ruled = Part.makeRuledSurface(self.edge1, self.edge2)
            self.rail1 = self.ruled.Edges[0]
            self.rail2 = self.ruled.Edges[2]
            self.u0 = self.ruled.ParameterRange[0]
            self.u1 = self.ruled.ParameterRange[1]
    def tangentsAt(self, p):
        return((self.rail1.tangentAt(p), self.rail2.tangentAt(p)))
    def normalsAt(self, p):
        return((self.ruled.normalAt(p,0), self.ruled.normalAt(p,1)))
    def binormalAt(self, p):
        v1 = self.rail1.valueAt(p)
        v2 = self.rail2.valueAt(p)
        return(v2.sub(v1))
    def frame1At(self, p):
        t = self.rail1.tangentAt(p)
        b = self.binormalAt(p)
        return((b, t, self.ruled.normalAt(p,0)))
    def frame2At(self, p):
        t = self.rail2.tangentAt(p)
        b = self.binormalAt(p)
        return((b, t, self.ruled.normalAt(p,1)))
    def matrix1At(self, p):
        t = self.rail1.valueAt(p)
        u,v,w = self.frame1At(p)
        m=App.Matrix( u.x,v.x,w.x,t.x,
                      u.y,v.y,w.y,t.y,
                      u.z,v.z,w.z,t.z,
                      0.0,0.0,0.0,1.0)
        return(m)
    def matrix2At(self, p):
        t = self.rail2.valueAt(p)
        u,v,w = self.frame2At(p)
        m=App.Matrix( u.x,v.x,w.x,t.x,
                      u.y,v.y,w.y,t.y,
                      u.z,v.z,w.z,t.z,
                      0.0,0.0,0.0,1.0)
        return(m)
    
    

myBirail = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Birail")
birail(myBirail)
