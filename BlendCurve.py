import math
import FreeCAD
import Part

def error(s):
    FreeCAD.Console.PrintError(s)

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
    
    def getChordLength(self):
        v1 = self.edge1.valueAt(self.param1)
        v2 = self.edge2.valueAt(self.param2)
        self.chordLength = v1.distanceToPoint(v2)
        if self.chordLength < 1e-4:
            self.chordLength = 1.0
    
    def getPoles(self): #, edge, param, cont, scale):
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
