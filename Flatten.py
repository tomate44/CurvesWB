
from operator import itemgetter

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

class sol:
    def __init__(self, face):
        self.face = face
        self.points = []
    def addSol(self, dts,d):
        print(" ")
        for sol in dts[2]:
            print("%s"%str(sol))
            if sol[3] == "Face":
                self.points.append((sol[5][0],FreeCAD.Vector(sol[2],d,0)))


rail = App.getDocument("Unnamed").getObject("Discretized_Edge")
pts = rail.Points
railDir = FreeCAD.Vector(0,100,0)

bs = Part.BSplineCurve()
for i in range(len(pts)):
    bs.setPole(i+1,FreeCAD.Vector(pts[i]))

Part.show(bs.toShape())

    


s = FreeCADGui.Selection.getSelection()
discCurves = []
for o in s:
    for f in o.Shape.Faces:
        discCurves.append(sol(f))


for i in range(len(pts)):
    d = 1.0 * i * rail.Distance
    pick = Part.Edge(Part.LineSegment(pts[i].sub(railDir),pts[i].add(railDir)))
    for discCurve in discCurves:
        dts = pick.distToShape(discCurve.face)
        if dts[0] <= 1e-6:
            discCurve.addSol(dts,d)

for disc in discCurves:
    sortedPts = sorted(disc.points,key=itemgetter(0))
    params = []
    vts = []
    for p in sortedPts:
        params.append(p[0])
        vts.append(Part.Vertex(p[1]))
#    bs = Part.BSplineCurve()
#    bs.interpolate(Points = pts, Parameters = params)
#    Part.show(bs.toShape())
    c = Part.Compound(vts)
    Part.show(c)



face = App.getDocument("test_flatten").getObject("Slice").Shape.Face2
edges = face.Edges

doc = App.ActiveDocument
rail = doc.getObject("Discretized_Edge")
pts = rail.Points
railDir = FreeCAD.Vector(0,100,0)
dis = rail.Distance

params = []

for i in range(len(pts)):
    #params.append(1.0 * i * dis)

bs = Part.BSplineCurve()
bs.interpolate(Points = pts, Parameters = params)

Part.show(bs.toShape())

c2d = []
for e in edges:
    c2d.append(face.curveOnSurface(e))

plane = Part.Plane()

for c in c2d:
    Part.show(c[0].toShape(plane,c[1],c[2]))


            
