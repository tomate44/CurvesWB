class ProfileShape:
    """Wrapper for shapes that will be used in a surfacing operation"""

    def __init__(self, shape, tol=1e-7):
        self.BaseShape = shape
        self.tol3d = tol
        self.full_bspline = None
        self.polygon = None
        self.BSplines = []
        self.compute_BSplines()

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

    # def get_max_edge_gap(self):
    #     maxgap = 0.0
    #     for i in range(self.NbEdges - 1):
    #         e = self.BaseShape.Edges[i]
    #         comp = Part.Compound(self.BaseShape.Edges[:i] + self.BaseShape.Edges[i + 1:])
    #         dist, pts, info = e.distToShape(comp)
    #         maxgap = max(maxgap, dist)
    #     return maxgap

    def compute_BSplines(self, rational=False):
        self.BSplines = []
        # Shape is a single Vertex
        if (self.NbEdges == 0):
            bs = Part.BSplineCurve()
            bs.setPole(1, self.BaseShape.Vertex1.Point)
            bs.setPole(2, self.BaseShape.Vertex1.Point)
            self.BSplines.append(bs)
        # Shape is a single Edge
        if (self.NbEdges == 1):
            e = self.BaseShape.Edge1
            if rational:
                e = self.BaseShape.Edge1.toNurbs().Edge1
            c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
            self.BSplines.append(c)
        # Shape is a single Wire
        elif (self.NbWires == 1):
            shape = self.BaseShape.Wire1
            if rational:
                shape = self.BaseShape.Wire1.toNurbs().Wire1
            for e in shape.OrderedEdges:
                c = e.Curve.toBSpline(e.FirstParameter, e.LastParameter)
                self.BSplines.append(c)
        c0 = self.BSplines[0]
        if len(self.BSplines) > 1:
            for c in self.BSplines[1:]:
                c0.join(c)
        self.full_bspline = c0
        self.compute_uniform_polygon()
        return self.full_bspline

    def compute_uniform_polygon(self):
        p = self.full_bspline.FirstParameter
        pts = [self.full_bspline.value(p)]
        pars = [0.0]
        if len(self.BSplines) > 1:
            for i, v in enumerate(self.BaseShape.OrderedVertexes[1:-1]):
                print(i)
                p = self.full_bspline.parameter(v.Point)
                print(p)
                pts.append(self.full_bspline.value(p))
                pars.append(float(i + 1))
        p = self.full_bspline.LastParameter
        pts.append(self.full_bspline.value(p))
        pars.append(pars[-1] + 1)
        mults = [1] * (len(pars))
        mults[0] = 2
        mults[-1] = 2
        bs = Part.BSplineCurve()
        print(pts, mults, pars)
        bs.buildFromPolesMultsKnots(pts, mults, pars, False, 1)
        self.polygon = bs
        return self.polygon



sel = FreeCADGui.Selection.getSelection()
o = sel[0]
swob = ProfileShape(o.Shape)
# print(swob.get_max_edge_gap())
Part.show(swob.full_bspline.toShape())
Part.show(swob.polygon.toShape())
