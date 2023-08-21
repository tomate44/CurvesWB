class ProfileShape:
    """Wrapper for shapes that will be used in a surfacing operation"""

    def __init__(self, shape, tol=1e-7):
        self.BaseShape = shape
        self.tol3d = tol

    @property
    def NbFaces(self):
        return len(self.BaseShape.Faces)

    @property
    def NbWires(self):
        return len(self.BaseShape.Wires)

    @property
    def NbEdges(self):
        return len(self.BaseShape.Edges)

    @property
    def NbVertexes(self):
        return len(self.BaseShape.Vertexes)

    def get_max_edge_gap(self):
        maxgap = 0.0
        for i in range(self.NbEdges - 1):
            e = self.BaseShape.Edges[i]
            comp = Part.Compound(self.BaseShape.Edges[:i] + self.BaseShape.Edges[i + 1:])
            dist, pts, info = e.distToShape(comp)
            maxgap = max(maxgap, dist)
        return maxgap

    def get_BSpline(self, rational=False):
        # Shape is a single Vertex
        if (self.NbEdges == 0):
            bs = Part.BSplineCurve()
            bs.setPole(1, self.BaseShape.Vertex1.Point)
            bs.setPole(2, self.BaseShape.Vertex1.Point)
            return bs
        # Shape is a single Wire
        if (self.NbWires == 1):
            shape = self.BaseShape.Wire1
            if rational:
                shape = self.BaseShape.Wire1.toNurbs().Wire1
            e0 = shape.OrderedEdges[0]
            c0 = e0.Curve.toBSpline(e0.FirstParameter, e0.LastParameter)
            for e in shape.OrderedEdges[1:]:
                c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
                c0.join(c)
            return c0
        # Shape is a single Edge
        if (self.NbEdges == 1):
            e = self.BaseShape.Edge1
            if rational:
                e = self.BaseShape.Edge1.toNurbs().Edge1
            c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
            return c



sel = FreeCADGui.Selection.getSelection()
o = sel[0]
swob = ProfileShape(o.Shape)
print(swob.get_max_edge_gap())
Part.show(swob.get_BSpline().toShape())
Part.show(swob.get_BSpline(True).toShape())
