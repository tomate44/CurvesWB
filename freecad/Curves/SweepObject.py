vec2 = FreeCAD.Base.Vector2d


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


class Path2Rails:
    def __init__(self, rail1, rail2):
        self.Rail1 = ProfileShape(rail1)
        self.Rail2 = ProfileShape(rail2)
        # self.Face1 = face1
        # self.Face2 = face2
        # self.TangentToFaces = False
        self.ReversedNormal = False
        ruled = Part.makeRuledSurface(self.Rail1.full_bspline.toShape(),
                                      self.Rail2.full_bspline.toShape())
        self.Surface = ruled.Surface
        self.Surface.scaleKnotsToBounds(0.0, 1.0)

    def origin(self):
        return self.Surface.value(u1, 0.0)

    def XPoint(self):
        return self.Surface.value(u2, 1.0)

    def get_transform_matrix(self, u1, u2, position=0.0):
        # obj.Rail1Length = e1.Length
        # obj.Rail2Length = e2.Length
        # p1 = e1.getParameterByLength(obj.Position1 * e1.Length)
        par1 = (u1, 0.0)
        par2 = (u2, 1.0)
        origin = self.Surface.value(u1, 0.0)
        ptX = self.Surface.value(u2, 1.0)
        rs = Part.makeRuledSurface(e1, e2)
        u0, v0 = rs.Surface.parameter(origin)
        normal = rs.Surface.normal(u0, obj.NormalPosition)
        if obj.NormalReverse:
            normal = -normal
        uiso = rs.Surface.uIso(u0)
        width = uiso.length()
        obj.ChordLength = width
        tangent = uiso.tangent(obj.NormalPosition)[0]
        bino = -normal.cross(tangent)
        # if obj.NormalReverse:
        #     bino = -bino
        m = FreeCAD.Matrix(tangent.x, normal.x, bino.x, origin.x,
                           tangent.y, normal.y, bino.y, origin.y,
                           tangent.z, normal.z, bino.z, origin.z,
                           0, 0, 0, 1)
        # print(m.analyze())
        line1 = Part.makeLine(FreeCAD.Vector(), FreeCAD.Vector(width, 0.0, 0.0))
        pt = FreeCAD.Vector(obj.NormalPosition * width, 0.0, 0.0)
        line2 = Part.makeLine(pt, pt + FreeCAD.Vector(0.0, width, 0.00))
        obj.Shape = Part.Compound([line1, line2])
        obj.Placement = FreeCAD.Placement(m)



sel = FreeCADGui.Selection.getSelection()
o = sel[0]
swob = ProfileShape(o.Shape)
# print(swob.get_max_edge_gap())
Part.show(swob.full_bspline.toShape())
Part.show(swob.polygon.toShape())
