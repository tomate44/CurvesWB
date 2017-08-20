# Nurbs library for FreeCAD
# Author : Christophe Grellier
# License : LGPL 2.1

import FreeCAD
import Part

class curve(object):
    '''Base class of nurbs curves'''
    def __init__(self, edge = None):
        if edge == None:
            v1 = FreeCAD.Vector(0,0,0)
            v2 = FreeCAD.Vector(1,0,0)
            b = Part.BezierCurve()
            b.setPoles([v1,v2])
            self.curve = b
        elif isinstance(edge, Part.Edge):
            c = edge.Curve
            if isinstance(c, (Part.BezierCurve, Part.BSplineCurve)):
                self.curve = c
            else:
                bs = c.toBSpline()
                self.curve = bs
        elif isinstance(edge, (Part.BezierCurve, Part.BSplineCurve)):
            self.curve = edge

    def lenght(self):
        return self.curve.lenght()




class curveOnSurface(curve):
    '''defines a curve on a surface'''


class isoCurve:
    '''isoCurve of a surface'''
    def __init__(self, face, direc = 'U', param = 0):
        self.face = None
        self.direction = 'U'
        self.parameter = 0
        if not isinstance(face, Part.Face):
            Msg("Error. Not a face")
        else:
            self.bounds = face.ParameterRange
            self.face = face
        if not direc in 'UV':
            Msg("Direction error")
        else:
            self.direction = direc
        if not isinstance(param, (float, int)):
            Msg("Parameter error")
        else:
            self.parameter = param
        
    def toShape(self):
        if self.direction == 'U':
            self.curve = self.face.Surface.uIso(self.parameter)
            prange = self.bounds[2:4]
        elif self.direction == 'V':
            self.curve = self.face.Surface.vIso(self.parameter)
            prange = self.bounds[0:2]
        return(self.curve.toShape(prange[0],prange[1]))

class multiIso:
    '''defines a set of multiple iso curves on a face'''
    def __init__(self, face, numu = 0, numv = 0):
        self.face = None
        self.paramu = []
        self.paramv = []
        self.uiso = []
        self.viso = []
        if not isinstance(face, Part.Face):
            Msg("Error. Not a face")
        else:
            self.bounds = face.ParameterRange
            self.face = face
        if numu:
            self.setNumberU(numu)
        if numv:
            self.setNumberV(numv)

    def computeU(self):
        self.uiso = []
        for u in self.paramu:
            self.uiso.append(isoCurve(self.face,'U',u))

    def computeV(self):
        self.viso = []
        for v in self.paramv:
            self.viso.append(isoCurve(self.face,'V',v))

    #def compute(self):
        #self.computeU()
        #self.computeV()

    def toShape(self):
        c = []
        for u in self.uiso:
            c.append(u.toShape())
        for v in self.viso:
            c.append(v.toShape())
        return(Part.Compound(c))

    def paramList(self, n, fp, lp):
        rang = lp-fp
        l = []
        if n == 1:
            l = [fp + rang / 2.0]
        elif n == 2:
            l = [fp,lp]
        elif n > 2:
            for i in range(n):
                l.append( fp + 1.0* i* rang / (n-1) )
        return(l)

    def setNumberU(self, n):
        fp = self.bounds[0]
        lp = self.bounds[1]
        self.paramu = self.paramList(n, fp, lp)
        self.computeU()

    def setNumberV(self, n):
        fp = self.bounds[2]
        lp = self.bounds[3]
        self.paramv = self.paramList(n, fp, lp)
        self.computeV()

    def setNumbers(self, nu, nv):
        self.setNumberU(nu)
        self.setNumberV(nv)
            


        
