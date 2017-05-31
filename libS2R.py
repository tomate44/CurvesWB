from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from operator import itemgetter

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

fac = 1.0
DEBUG = False
EXTEND = True

class profile:
    
    def __init__(self, curve):
        self.realCurve = curve
        self.localCurve1 = None
        self.localCurve2 = None
        self.Rail1Param = 0.0
        self.Rail2Param = 0.0

class birail:
    
    def __init__(self, ruledSurf):
        self.ruled = ruledSurf
        self.rails = (ruledSurf.Edges[0], ruledSurf.Edges[2])
        self.normTan = False
        self.normBin = False
        self.normNor = True

    def tangentAt(self, p, i):
        if self.normTan:
            return(self.rails[i].tangentAt(p))
        else:
            return(self.rails[i].derivative1At(p))
        
    def normalAt(self, p, i):
        v = self.ruled.ParameterRange[2:]
        n = self.ruled.normalAt(p,v[i]).negative()
        if self.normNor:
            n.normalize()
        return(n)
    
    def binormalAt(self, p, i):
        # TODO check for 0-length vector
        v1 = self.rails[0].valueAt(p)
        v2 = self.rails[1].valueAt(p)
        v = v2.sub(v1)
        if self.normBin:
            v.normalize()
        if i == 0:
            return(v)
        elif i == 1:
            return(v.negative())

    def frameAt(self, p, i):
        t = self.tangentAt(p,i)
        b = self.binormalAt(p,i)
        n = self.normalAt(p,i)
        return((b, t, n))

    def matrixAt(self, p, i):
        t = self.rails[i].valueAt(p)
        u,v,w = self.frameAt(p,i)
        m = FreeCAD.Matrix( u.x, v.x, w.x, t.x,
                            u.y, v.y, w.y, t.y,
                            u.z, v.z, w.z, t.z,
                            0.0, 0.0, 0.0, 1.0)
        return(m)
    

class SweepOn2Rails:
    
    def __init__(self):
        self.birail = None
        self.interpoCurves = []
        self.profiles = []
        self.extend = False
        self.profileSamples = 20
        self.railSamples = 40
        
    def setRails(self, ruledSurf):
        # TODO: Check for twisted Ruled Surface
        self.birail = birail(ruledSurf)
        
    def setProfiles(self, plist):
        data = []
        self.knots1, self.knots2 = [],[]
        for pro in plist:
            dts1 = pro.realCurve.distToShape(self.birail.rails[0])
            dts2 = pro.realCurve.distToShape(self.birail.rails[1])
            FreeCAD.Console.PrintMessage('\nProfile :\n%s\n%s\n'%(str(dts1),str(dts2)))
            sols1 = dts1[1][0]
            sols2 = dts2[1][0]
            #FreeCAD.Console.PrintMessage("%s\n"%str(sols1))
            k1 = self.birail.rails[0].Curve.parameter(sols1[1])
            k2 = self.birail.rails[1].Curve.parameter(sols2[1])
            data.append((k1,k2,pro))
        sortedProfs = sorted(data,key=itemgetter(0))
        self.profiles = []
        for datum in sortedProfs:
            self.knots1.append(datum[0])
            self.knots2.append(datum[1])
            p = profile(datum[2])
            p.Rail1Param = datum[0]
            p.Rail2Param = datum[1]
            self.profiles.append(p)
        if len(plist) == 1:
            self.extend = True
        FreeCAD.Console.PrintMessage('\nProfiles sorted\n')

    def getLocalProfile(self, pro):
        m1 = self.birail.matrixAt(pro.Rail1Param,0)
        m2 = self.birail.matrixAt(pro.Rail1Param,1)
        pts = pro.realCurve.Curve.getPoles()
        c1 = pro.realCurve.Curve.copy()
        c2 = pro.realCurve.Curve.copy()
        for i in range(len(pts)):
            #np = m1.inverse().multiply(p)
            c1.setPole(i+1, m1.inverse().multiply(p))
            c2.setPole(i+1, m2.inverse().multiply(p))
        pro.localCurve1 = Part.Edge(c1, pro.realCurve.FirstParameter, pro.realCurve.LastParameter)
        pro.localCurve2 = Part.Edge(c2, pro.realCurve.FirstParameter, pro.realCurve.LastParameter)

    def getLocalProfiles(self):
        for pro in self.profiles:
            self.getLocalProfile(pro)

    def extendProfiles(self):
        p0 = self.profiles[0]
        p1 = self.profiles[-1]
        if (not p0.Rail1Param == self.birail.rails[0].FirstParameter) and (not p0.Rail2Param == self.birail.rails[1].FirstParameter):
            p = profile(p0.realCurve)
            p.Rail1Param = self.birail.rails[0].FirstParameter
            p.Rail2Param = self.birail.rails[1].FirstParameter
            p.localCurve1 = p0.localCurve1
            p.localCurve2 = p0.localCurve2
            # Warning : p.realCurve is wrong here
            self.profiles.insert(0,p)
        if (not p1.Rail1Param == self.birail.rails[0].LastParameter) and (not p1.Rail2Param == self.birail.rails[1].LastParameter):
            p = profile(p1.realCurve)
            p.Rail1Param = self.birail.rails[0].LastParameter
            p.Rail2Param = self.birail.rails[1].LastParameter
            p.localCurve1 = p1.localCurve1
            p.localCurve2 = p1.localCurve2
            # Warning : p.realCurve is wrong here
            self.profiles.append(p)

    def translateLocalProfiles(self, vec):
        for i in range(len(self.profiles)):
            pro = self.profiles[i]
            v = FreeCAD.Vector(vec)
            v.multiply(i)
            pro.localCurve1.translate(v)
            pro.localCurve2.translate(v)

    def railsInfo(self):
        FreeCAD.Console.PrintMessage('\nInfo Rail 1\n')
        FreeCAD.Console.PrintMessage('knots : %s\n'%(str(self.knots1)))
        FreeCAD.Console.PrintMessage('\nInfo Rail 2\n')
        FreeCAD.Console.PrintMessage('knots : %s\n'%(str(self.knots2)))
        
    def profilesInfo(self):
        pass
    
    def build(self):
        self.getLocalProfiles()
        if self.extend:
            self.extendProfiles()
        self.translateLocalProfiles(FreeCAD.Vector(0,1,0))
        self.buildInterpoCurves()
        
        
        pts1 = []
        pts2 = []
        interpo1 = []
        interpo2 = []
        #self.pointArray = []
        for ri in range(self.profileSamples):
            pts = self.getProfPoints(obj, ri)
            localpts = self.localCoords(pts)
            interpoCurves = self.interpolate(localpts)
            interpo1.append(Part.Edge(interpoCurves[0]))
            interpo2.append(Part.Edge(interpoCurves[1]))
            dis = self.discretize(obj, interpoCurves)
            #worldpts = self.worldCoords(pts)
            pts1 += dis[0] #pts1.append(dis[0])
            pts2 += dis[1] #pts2.append(dis[1])
        finalpts = []
        if   obj.Blending == "Rail1":
            finalpts = pts1
        elif obj.Blending == "Rail2":
            finalpts = pts2
        elif obj.Blending == "Average":
            for i in range(len(pts1)):
                finalpts.append((pts1[i]+pts2[i]).multiply(0.5))
        elif obj.Blending == "Blend":
            for i in range(len(pts1)):
                f = 1.0*(i/obj.RailSamples)/obj.ProfileSamples
                finalpts.append(pts1[i].multiply(f)+pts2[i].multiply(1.0-f))
        v = [Part.Vertex(p) for p in finalpts]
        c = Part.Compound(v) #+interpo1+interpo2)
        if DEBUG:
            dc1 = Part.Compound(interpo1)
            dc2 = Part.Compound(interpo2)
            Part.show(dc1)
            Part.show(dc2)
        obj.Shape = c



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
        obj.RailSamples = 40
        self.birail = None
        self.profiles = None

    def getProfPoints(self, obj, i):
        pts = []
        for p in self.profiles:
            if True: #p.Orientation == "Forward":
                v0 = p.FirstParameter
                v1 = p.LastParameter
            else:
                v1 = p.FirstParameter
                v0 = p.LastParameter
            pRange = v1-v0
            t = v0 + 1.0 * pRange * i / (obj.ProfileSamples-1)
            pts.append(p.valueAt(t))
        return(pts)

    def localCoords(self, pts):

        #pr1 = self.birail.Proxy.rail1.ParameterRange
        #pr2 = self.birail.Proxy.rail2.ParameterRange
        #if (not self.knots1[0] == pr1[0]) and (not self.knots2[0] == pr2[0]):
            #self.knots1.insert(0,pr1[0])
            #self.knots2.insert(0,pr2[0])
            #p = pts[0]
        #data = []   
        out1 = []
        out2 = []
        for i,p in enumerate(pts):
            m1 = self.birail.Proxy.matrix1At(self.knots1[i])
            m2 = self.birail.Proxy.matrix2At(self.knots2[i])
            p1 = m1.inverse().multiply(p)
            p2 = m2.inverse().multiply(p)
            p3 = FreeCAD.Vector(p1.x, p1.y+self.knots1[i]*fac, p1.z)
            p4 = FreeCAD.Vector(p2.x, p2.y+self.knots2[i]*fac, p2.z)
            out1.append(p3)
            out2.append(p4)
            #data.append((p1,p2,self.knots1[i],self.knots2[i]))
        #if (not data[0][2] == pr1[0]) and (not data[0][3] == pr2[0]):
            #d = (data[0][0],data[0][1],pr1[0],pr2[0])
            #data.insert(0,d)
        #if (not data[-1][2] == pr1[1]) and (not data[-1][3] == pr2[1]):
            #d = (data[-1][0],data[-1][1],pr1[1],pr2[1])
            #data.append(d) 
        #out1 = []
        #out2 = []
        #self.knots1 = []
        #self.knots2 = []
        #for p1,p2,k1,k2 in data:
            #p3 = FreeCAD.Vector(p1.x, p1.y+k1*fac, p1.z)
            #p4 = FreeCAD.Vector(p2.x, p2.y+k2*fac, p2.z)
            #out1.append(p3)
            #out2.append(p4)
            #self.knots1.append(k1)
            #self.knots2.append(k2)
        return(out1, out2)

    def interpolate(self, pts):
        #v = [FreeCAD.Vector(0,1,0)] * len(pts[0])
        #b = [True] * len(pts[0])
        #b[0] = True
        #b[-1] = True

        p1 = pts[0][:]
        k1 = self.knots1[:]
        pr1 = self.birail.Proxy.rail1.ParameterRange

        p2 = pts[1][:]
        k2 = self.knots2[:]
        pr2 = self.birail.Proxy.rail2.ParameterRange
        
        if (len(p1) == 1) or EXTEND:
            if (not k1[0] == pr1[0]) and (not k2[0] == pr2[0]):
                p1.insert(0,FreeCAD.Vector(p1[0].x, p1[0].y+(pr1[0]-k1[0])*fac, p1[0].z))
                p2.insert(0,FreeCAD.Vector(p2[0].x, p2[0].y+(pr2[0]-k2[0])*fac, p2[0].z))
                k1.insert(0,pr1[0])
                k2.insert(0,pr2[0])
            if (not k1[-1] == pr1[1]) and (not k2[-1] == pr2[1]):
                p1.append(FreeCAD.Vector(p1[-1].x, p1[-1].y+(pr1[1]-k1[-1])*fac, p1[-1].z))
                p2.append(FreeCAD.Vector(p2[-1].x, p2[-1].y+(pr2[1]-k2[-1])*fac, p2[-1].z))
                k1.append(pr1[1])
                k2.append(pr2[1])
        #FreeCAD.Console.PrintMessage('interpolate\n%s\n%s\n'%(pts[0],self.knots1))
        #m = [1]*len(self.knots1)
        #m[0]  = 2
        #m[-1] = 2
        #c1.buildFromPolesMultsKnots(pts[0],m,self.knots1,False,1)
        FreeCAD.Console.PrintMessage('\n\n%s\n%s\n'%(str(p1),str(k1)))
        
        c1 = Part.BSplineCurve()
        c1.interpolate(Points = p1, Parameters = k1) #, Tangents = v, TangentFlags = b)
        c2 = Part.BSplineCurve()
        #c2.buildFromPolesMultsKnots(pts[1],m,self.knots2,False,1)
        c2.interpolate(Points = p2, Parameters = k2) #, Tangents = v, TangentFlags = b)
        return(c1,c2)        

    def discretize(self, obj, c):
        pts1 = []
        pts2 = []
        for i in range(obj.RailSamples):
            v0 = self.knots1[0]
            v1 = self.knots1[-1]
            pRange1 = v1-v0
            t1 = v0 + 1.0 * pRange1 * i / (obj.RailSamples-1)
            v2 = self.knots2[0]
            v3 = self.knots2[-1]
            pRange2 = v3-v2
            t2 = v2 + 1.0 * pRange2 * i / (obj.RailSamples-1)
            pt1 = Part.Edge(c[0]).valueAt(t1)
            m1 = self.birail.Proxy.matrix1At(t1)
            pts1.append(m1.multiply(FreeCAD.Vector(pt1.x, pt1.y-t1*fac, pt1.z)))
            pt2 = Part.Edge(c[1]).valueAt(t2)
            m2 = self.birail.Proxy.matrix2At(t2)
            pts2.append(m2.multiply(FreeCAD.Vector(pt2.x, pt2.y-t2*fac, pt2.z)))
        return(pts1,pts2)

    def execute(self, obj):
        self.birail = obj.Birail
        self.setProfiles(obj.Profiles)
        self.setParams()
        pts1 = []
        pts2 = []
        interpo1 = []
        interpo2 = []
        #self.pointArray = []
        for ri in range(obj.ProfileSamples):
            pts = self.getProfPoints(obj, ri)
            localpts = self.localCoords(pts)
            interpoCurves = self.interpolate(localpts)
            interpo1.append(Part.Edge(interpoCurves[0]))
            interpo2.append(Part.Edge(interpoCurves[1]))
            dis = self.discretize(obj, interpoCurves)
            #worldpts = self.worldCoords(pts)
            pts1 += dis[0] #pts1.append(dis[0])
            pts2 += dis[1] #pts2.append(dis[1])
        finalpts = []
        if   obj.Blending == "Rail1":
            finalpts = pts1
        elif obj.Blending == "Rail2":
            finalpts = pts2
        elif obj.Blending == "Average":
            for i in range(len(pts1)):
                finalpts.append((pts1[i]+pts2[i]).multiply(0.5))
        elif obj.Blending == "Blend":
            for i in range(len(pts1)):
                f = 1.0*(i/obj.RailSamples)/obj.ProfileSamples
                finalpts.append(pts1[i].multiply(f)+pts2[i].multiply(1.0-f))
        v = [Part.Vertex(p) for p in finalpts]
        c = Part.Compound(v) #+interpo1+interpo2)
        if DEBUG:
            dc1 = Part.Compound(interpo1)
            dc2 = Part.Compound(interpo2)
            Part.show(dc1)
            Part.show(dc2)
        obj.Shape = c
                

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
            data = []
            self.knots1, self.knots2 = [],[]
            for pro in self.profiles:
                dts1 = pro.distToShape(self.birail.Shape.Edges[0])
                dts2 = pro.distToShape(self.birail.Shape.Edges[2])
                FreeCAD.Console.PrintMessage('\nProfile :\n%s\n%s\n'%(str(dts1),str(dts2)))
                sols1 = dts1[1][0]
                sols2 = dts2[1][0]
                #FreeCAD.Console.PrintMessage("%s\n"%str(sols1))
                k1 = self.birail.Shape.Edges[0].Curve.parameter(sols1[1])
                k2 = self.birail.Shape.Edges[2].Curve.parameter(sols2[1])
                data.append((k1,k2,pro))
            sortedProfs = sorted(data,key=itemgetter(0))
            self.profiles = []
            for datum in sortedProfs:
                self.knots1.append(datum[0])
                self.knots2.append(datum[1])
                self.profiles.append(datum[2])
            FreeCAD.Console.PrintMessage('\nknots :\n%s\n%s\n'%(str(self.knots1),str(self.knots2)))

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

class s2rCommand:
    def parseSel(self, selectionObject):
        birail = None
        profs = []
        for obj in selectionObject:
            if hasattr(obj,"NormalizeBinormal"): #if isinstance(obj.Proxy, birail):
                birail = obj
            else:
                profs.append(obj)
        return((birail,profs))

    def Activated(self):
        myS2R = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Sweep 2 rails")
        sweep2rails(myS2R)
        sweep2railsVP(myS2R.ViewObject)

        s = FreeCADGui.Selection.getSelection()
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







