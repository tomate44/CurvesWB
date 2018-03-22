import math
import FreeCAD
import Part
import bsplineBasis

def error(s):
    FreeCAD.Console.PrintError(s)

def curvematch(c1, c2, par1, level=0, scale=1.0):

    c1 = c1.toNurbs()
    c2 = c2.toNurbs()

    #c1end = 2.5 #c1.LastParameter
    c2sta = c2.FirstParameter

    p1 = c1.getPoles()
    p2 = c2.getPoles()

    #seq = c2.KnotSequence
    seq = [k*scale for k in c2.KnotSequence]
    if scale < 0:
        seq.reverse()
        p2 = p2[::-1]

    #basis1 = splipy.BSplineBasis(order=int(c1.Degree)+1, knots=c1.KnotSequence)
    #basis2 = splipy.BSplineBasis(order=int(c2.Degree)+1, knots=seq)
    basis1 = bsplineBasis.bsplineBasis()
    basis2 = bsplineBasis.bsplineBasis()
    basis1.p = c1.Degree
    basis1.U = c1.KnotSequence
    basis2.p = c2.Degree
    basis2.U = seq

    l = 0
    while l <= level:
        FreeCAD.Console.PrintMessage("\nDerivative %d\n"%l)
        ev1 = basis1.evaluate(par1,d=l) #.A1.tolist()
        ev2 = basis2.evaluate(c2sta,d=l) #.A1.tolist()
        FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev1))
        FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev2))
        pole1 = FreeCAD.Vector()
        for i in range(len(ev1)):
            pole1 += 1.0*ev1[i]*p1[i]
        val = ev2[l]
        if val == 0:
            FreeCAD.Console.PrintError("Zero !\n")
            break
        else:
            pole2 = FreeCAD.Vector()
            for i in range(l):
                pole2 += 1.0*ev2[i]*p2[i]
            np = (1.0*pole1-pole2)/val
            FreeCAD.Console.PrintMessage("Moving P%d from (%0.2f,%0.2f,%0.2f) to (%0.2f,%0.2f,%0.2f)\n"%(l,p2[l].x,p2[l].y,p2[l].z,np.x,np.y,np.z))
            p2[l] = np
        l += 1
    nc = c2.copy()
    for i in range(len(p2)):
        nc.setPole(i+1,p2[i])
    return(nc)

class blendCurve:
    def __init__(self, e1 = None, e2 = None):
        if e1 and e2:
            self.edge1 = e1
            self.edge2 = e2
            self.param1 = e1.FirstParameter
            self.param2 = e2.FirstParameter
            self.cont1 = 0
            self.cont2 = 0
            self.scale1 = 1.0
            self.scale2 = 1.0
            self.bezier = Part.BezierCurve()
            self.getChordLength()
            self.autoScale = True
        else:
            error("blendCurve initialisation error")
    
    def getChord(self):
        v1 = self.edge1.valueAt(self.param1)
        v2 = self.edge2.valueAt(self.param2)
        ls = Part.LineSegment(v1,v2)
        return(ls)
    
    def getChordLength(self):
        ls = self.getChord()
        self.chordLength = ls.length()
        if self.chordLength < 1e-6:
            self.chordLength = 1.0

    def getPoles(self):
        nbPoles = self.cont1 + self.cont1 + 2
        #knotSeq = [0.0 for x in range(nbPoles)]
        #knotSeq2 = [1.0 for x in range(nbPoles)]
        #knotSeq.extend(knotSeq2)
        be = Part.BezierCurve()
        be.increase(nbPoles-1)
        #bs = be.toBSpline()
        nc = curvematch(self.edge1.Curve, be, self.param1, self.cont1, self.scale1)
        be = Part.BezierCurve()
        be.setPoles(nc.getPoles()[::-1])
        nc = curvematch(self.edge2.Curve, be, self.param2, self.cont2, self.scale2)
        return(nc.getPoles())
        

    def getPolesOld(self): #, edge, param, cont, scale):
        poles1 = []
        poles2 = []
        poles1.append(self.edge1.valueAt(self.param1))
        poles2.append(self.edge2.valueAt(self.param2))
        if self.cont1 > 0:
            t1 = self.edge1.tangentAt(self.param1)
            t1.normalize().multiply(self.unitLength * self.scale1)
            poles1.append(poles1[0].add(t1))
        if self.cont2 > 0:
            t2 = self.edge2.tangentAt(self.param2)
            t2.normalize().multiply(self.unitLength * self.scale2)
            poles2.append(poles2[0].add(t2))
        if self.cont1 > 1:
            curv = self.edge1.curvatureAt(self.param1)
            if curv:
                radius = curv * self.nbSegments * pow(t1.Length,2) / (self.nbSegments -1)
                opp = math.sqrt(abs(pow(self.unitLength * self.scale1,2)-pow(radius,2)))
                c = Part.Circle()
                c.Axis = t1
                v = FreeCAD.Vector(t1)
                v.normalize().multiply(t1.Length+opp)
                c.Center = poles1[0].add(v)
                c.Radius = radius
                plane = Part.Plane(poles1[0],poles1[1],poles1[0].add(self.edge1.normalAt(self.param1)))
                print(plane)
                pt = plane.intersect(c)[0][1] # 2 solutions
                print(pt)
                poles1.append(FreeCAD.Vector(pt.X,pt.Y,pt.Z))
            else:
                poles1.append(poles1[-1].add(t1))
        if self.cont2 > 1:
            curv = self.edge2.curvatureAt(self.param2)
            if curv:
                radius = curv * self.nbSegments * pow(t2.Length,2) / (self.nbSegments -1)
                opp = math.sqrt(abs(pow(self.unitLength * self.scale2,2)-pow(radius,2)))
                c = Part.Circle()
                c.Axis = t2
                v = FreeCAD.Vector(t2)
                v.normalize().multiply(t2.Length+opp)
                c.Center = poles2[0].add(v)
                c.Radius = radius
                plane = Part.Plane(poles2[0],poles2[1],poles2[0].add(self.edge2.normalAt(self.param2)))
                print(plane)
                pt = plane.intersect(c)[0][1] # 2 solutions
                print(pt)
                poles2.append(FreeCAD.Vector(pt.X,pt.Y,pt.Z))
            else:
                poles2.append(poles2[-1].add(t2))
            #if len(poles1) > 1:
                #poles2.append(c.value(c.parameter(poles1[-2])))
            #else:
                #poles2.append(c.value(c.parameter(poles1[0])))
        return(poles1+poles2[::-1])
            
    def compute(self):
        if self.autoScale:
            self.getChordLength()
        self.nbSegments = 1 + self.cont1 + self.cont2
        self.unitLength = self.chordLength / self.nbSegments
        poles = self.getPoles() #self.edge1, self.param1, self.cont1, self.scale1)
        self.bezier.setPoles(poles)

    def shape(self):
        self.compute()
        return(self.bezier.toShape())

    def curve(self):
        self.compute()
        return(self.bezier)

#obj1 = App.getDocument("Surface_test_1").getObject("Sphere001")
#e1 = obj1.Shape.Edge2
#e2 = obj1.Shape.Edge4

#bc = blendCurve(e1,e2)
#bc.param1 = e1.LastParameter
#bc.param2 = e2.LastParameter
#bc.cont1 = 2
#bc.cont2 = 2
#bc.scale1 = 1.5
#bc.scale2 = 1.5
#Part.show(bc.shape())

#e = []
#sel = FreeCADGui.Selection.getSelectionEx()
#for selobj in sel:
    #if selobj.HasSubObjects:
        #for sub in selobj.SubObjects:
            #e.append(selobj.Object.Shape)
