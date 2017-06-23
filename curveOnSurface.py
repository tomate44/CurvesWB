from __future__ import division # allows floating point division from integers
import FreeCAD
import Part
from FreeCAD import Base



#Find the minimum distance to another shape.
#distToShape(Shape s):  Returns a list of minimum distance and solution point pairs.
#
#Returned is a tuple of three: (dist, vectors, infos).
#
#dist is the minimum distance, in mm (float value).
#
#vectors is a list of pairs of App.Vector. Each pair corresponds to solution.
#Example: [(Vector (2.0, -1.0, 2.0), Vector (2.0, 0.0, 2.0)), (Vector (2.0,
#-1.0, 2.0), Vector (2.0, -1.0, 3.0))] First vector is a point on self, second
#vector is a point on s.
#
#infos contains additional info on the solutions. It is a list of tuples:
#(topo1, index1, params1, topo2, index2, params2)
#
#    topo1, topo2 are strings identifying type of BREP element: 'Vertex',
#    'Edge', or 'Face'.
#
#    index1, index2 are indexes of the elements (zero-based).
#
#    params1, params2 are parameters of internal space of the elements. For
#    vertices, params is None. For edges, params is one float, u. For faces,
#    params is a tuple (u,v). 



class curveOnSurface:
    
    def __init__(self, face = None, edge = None):
        self.face = face
        self.edge = edge
        self.curve2D = None
        self.validate()
        self.reverseTangent  = False
        self.reverseNormal   = False
        self.reverseBinormal = False

    def setEdge(self, edge):
        self.edge = edge

    def setFace(self, face):
        self.face = face

    def validate(self):
        if (not self.edge == None) and (not self.face == None):
            self.curve2D = self.face.curveOnSurface(self.edge)
            if not isinstance(self.curve2D,list):
                self.curve2D = None

    def valueAt(self, t):
        if self.edge:
            return(self.edge.valueAt(t))
        else:
            return(None)

    def tangentAt(self, t):
        if self.edge:
            if self.reverseTangent:
                return(self.edge.tangentAt(t).negative())
            else:
                return(self.edge.tangentAt(t))
        else:
            return(None)

    def normalAt(self, t):
        if self.edge:
            vec = None
            if self.face:
                if self.curve2D:
                    p = self.curve2D[0].value(t)
                    vec = self.face.normalAt(p.x,p.y)
                else:
                    # TODO Try to get self.face normal using distToShape
                    # v = Part.Vertex(self.edge.valueAt(t))
                    # d, pts, info = v.distToShape(self.face)
                    # if info[0]:
                    pass
            else:
                vec = self.edge.normalAt(t)
            if self.reverseNormal:
                return(vec.negative())
            else:
                return(vec)
        else:
            return(None)

    def binormalAt(self, t):
        t = self.tangentAt(t)
        n = self.normalAt(t)
        if (not t == None) and (not n == None):
            if self.reverseBinormal:
                return(t.cross(n).negative())
            else:
                return(t.cross(n))
        else:
            return(None)



     
