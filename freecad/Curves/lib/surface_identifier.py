import FreeCAD
import Part
from random import random
from math import pi


def mean_vector(vectors):
    "Return the mean vector of a list of vectors"
    point = FreeCAD.Vector()
    for pt in vectors:
        point += pt
    point /= len(vectors)
    return point


def mean_line(lines):
    "Return the mean line of a list of lines"
    direction = mean_vector([li.Direction for li in lines])
    location = mean_vector([li.Location for li in lines])
    return Part.Line(location, location + direction)


def lines_intersection(lines, tol=1e-7, size=1e6):
    """
    If lines all intersect into one point.
    Returns this point, or None otherwise.
    Input :
    lines : list of Part.Line
    tol (float): search tolerance
    size (float): size for edge conversion
    Return :
    Converging point (FreeCAD.Vector) or None
    """
    interlist = []
    for i in range(len(lines) - 1):
        li1 = lines[i].toShape(-size, size)
        li2 = lines[i + 1].toShape(-size, size)
        d, pts, info = li1.distToShape(li2)
        # Part.show(Part.Compound([li1, li2]))
        if d > tol:
            # print(f"Find_apex 1, intersection #{i} : {d} out of tolerance {tol}")
            # Part.show(Part.Compound([li1, li2]))
            return None
        interlist.append(0.5 * pts[0][0] + 0.5 * pts[0][1])
    for i in range(len(interlist) - 1):
        d = interlist[i].distanceToPoint(interlist[i + 1])
        if d > tol:
            # print(f"Find_apex 2, intersection #{i} : {d} out of tolerance {tol}")
            return None
    return mean_vector(interlist)


def planes_intersection(planes, tol=1e-7):
    """
    If planes all intersect into one line, return this line.
    If planes intersect into parallel lines, return the direction.
    Else, return None
    Input :
    planes : list of Part.Plane
    tol (float): search tolerance
    Return :
    Intersection line (Part.Line)
    or intersection direction (FreeCAD.Vector)
    or None
    """
    center = None
    interlist = []
    for i in range(len(planes) - 1):
        inter = planes[i].intersect(planes[i + 1])
        interlist.extend(inter)
    if len(interlist) == 0:
        # All planes are parallel
        return None
    # Part.show(Part.Compound([il.toShape(-100, 100) for il in interlist]))
    coincident = True
    for i in range(len(interlist) - 1):
        i1 = interlist[i]
        i2 = interlist[i + 1]
        dotprod = i1.Direction.dot(i2.Direction)
        if (1.0 - abs(dotprod)) > tol:
            # print(f"plane intersection #{i}: out of tolerance {tol}")
            return None
        if dotprod < 0:
            i2.reverse()
        if i1.Location.distanceToLine(i2.Location, i2.Direction) > tol:
            coincident = False
    axis = mean_vector([li.Direction for li in interlist])
    # print(f"Found Axis {axis}")
    if coincident:
        center = mean_vector([li.Location for li in interlist])
        # print(f"Found Center {center}")
        return Part.Line(center, center + axis)
    return axis


class SurfaceIdentifier:
    "Tries to identify canonical surface of a face"

    def __init__(self, face, num_samples=10, tol=1e-7):
        self.face = face
        self.num_samples = num_samples
        self.bounds = self.face.ParameterRange
        self.tol = tol
        self.Axis = None
        self.Apex = None
        self.SemiAngle = None
        self.Center = None
        self.Radius = None
        self._log = []

    def report(self):
        "Print the log stack"
        def prmes(mes):
            FreeCAD.Console.PrintMessage(mes + "\n")
        # prmes("*** SurfaceIdentifier Report")
        for line in self._log:
            prmes(f"- {line}")
        # prmes("***")

    def log(self, message):
        "Add message to the log stack"
        self._log.append(f"{str(message)}")

    def vecstr(self, vec, num_dec=3):
        "String representation of a Vector with fixed number of decimals"
        return f"({vec.x:.{num_dec}f}, {vec.y:.{num_dec}f}, {vec.z:.{num_dec}f})"

    def is_canonical(self):
        types = ('Part::GeomPlane',
                 'Part::GeomCylinder',
                 'Part::GeomCone',
                 'Part::GeomSphere'
                 'Part::GeomToroid')
        if self.face.Surface.TypeId in types:
            return True
        return False

    def uniform_UV(self):
        "Uniform generator of (u, v) parameters in the source face bounds"
        i = 0
        u0, u1, v0, v1 = self.bounds
        urange = u1 - u0
        vrange = v1 - v0
        for i in range(self.num_samples):
            u = u0 + i * urange / (self.num_samples - 1)
            v = v0 + i * vrange / (self.num_samples - 1)
            i += 1
            yield u, v

    def random_UV(self):
        "Random generator of (u, v) parameters in the source face bounds"
        i = 0
        u0, u1, v0, v1 = self.bounds
        urange = u1 - u0
        vrange = v1 - v0
        while i < self.num_samples:
            u = u0 + random() * urange
            v = v0 + random() * vrange
            i += 1
            yield u, v

    def sample_lines(self):
        "Return a list of lines along minimal curvature of source face"
        lines = []
        for u, v in self.uniform_UV():
            lines.append(self.min_curva_line(u, v))
        return lines

    def sample_planes(self):
        "Return a list of planes normal to maximal curvature of source face"
        planes = []
        for u, v in self.uniform_UV():
            planes.append(self.max_curva_plane(u, v))
        return planes

    def surface_point(self, u, v):
        return self.face.valueAt(u, v)

    def curva_dir(self, u, v):
        "Return maximal and minimal curvature directions at (u,v)"
        macudi, micudi = self.face.Surface.curvatureDirections(u, v)
        macu = abs(self.face.Surface.curvature(u, v, "Max"))
        micu = abs(self.face.Surface.curvature(u, v, "Min"))
        if (macudi.Length < self.tol) or (micudi.Length < self.tol):
            self.log(f"Curvature Directions Error: ({macudi}, {micudi})")
        if macu < micu:
            return micudi, macudi
        return macudi, micudi

    def min_curva_line(self, u, v):
        "Return a line along minimal curvature at (u,v)"
        pt = self.surface_point(u, v)
        di = self.curva_dir(u, v)[1]
        # print(pt, di)
        return Part.Line(pt, pt + di)

    def max_curva_line(self, u, v):
        "Return a line along maximal curvature at (u,v)"
        pt = self.surface_point(u, v)
        di = self.curva_dir(u, v)[0]
        return Part.Line(pt, pt + di)

    def min_curva_plane(self, u, v):
        "Return a plane normal to minimal curvature at (u,v)"
        pt = self.surface_point(u, v)
        di = self.curva_dir(u, v)[1]
        return Part.Plane(pt, di)

    def max_curva_plane(self, u, v):
        "Return a plane normal to maximal curvature at (u,v)"
        pt = self.surface_point(u, v)
        di = self.curva_dir(u, v)[0]
        return Part.Plane(pt, di)

    def fix_axis_orientation(self, axis):
        pt1 = self.face.valueAt(self.bounds[0], self.bounds[2])
        pt2 = self.face.valueAt(self.bounds[1], self.bounds[3])
        proj1 = axis.projectPoint(pt1)
        proj2 = axis.projectPoint(pt2)
        par1 = axis.parameter(proj1)
        par2 = axis.parameter(proj2)
        if par2 < par1:
            return Part.Line(proj2, proj2 - axis.Direction)
        return Part.Line(proj1, proj1 + axis.Direction)

    def cone_data(self, apex, axis):
        "Compute semi-angle, center and radius of a cone"
        axis_line = Part.Line(apex, apex + axis.Direction)
        pt1 = self.face.valueAt(self.bounds[0], self.bounds[2])
        pt2 = self.face.valueAt(self.bounds[1], self.bounds[3])
        proj1 = axis_line.projectPoint(pt1)
        proj2 = axis_line.projectPoint(pt2)
        par1 = axis_line.parameter(proj1)
        par2 = axis_line.parameter(proj2)
        # print(par1, par2)
        radius1 = pt1.distanceToPoint(proj1)
        radius2 = pt2.distanceToPoint(proj2)
        line1 = FreeCAD.Vector(0, par2 - par1, 0)
        line2 = FreeCAD.Vector(radius2, par2, 0) - FreeCAD.Vector(radius1, par1, 0)
        return line1.getAngle(line2), proj1, radius1

    def basis_curve(self):
        "Returns the basis curve of a surface of extrusion"
        u0, u1, v0, v1 = self.bounds
        pt = self.face.valueAt(0.5 * (u0 + u1), 0.5 * (v0 + v1))
        plane = Part.Plane(pt, self.Direction)
        intersect = plane.intersectSS(self.face.Surface)
        return intersect

    # Get canonical surfaces

    def get_sphere(self):
        lines = []
        for u, v in self.uniform_UV():
            p1 = self.face.valueAt(u, v)
            n = self.face.normalAt(u, v)
            li = Part.Line(p1, p1 + n)
            lines.append(li)
        center = lines_intersection(lines)
        if center is None:
            return
        pt = self.face.valueAt(self.bounds[0], self.bounds[2])
        radius = pt.distanceToPoint(center)
        sph = Part.Sphere()
        sph.Center = center
        sph.Radius = radius
        return sph

    def get_plane(self):
        if self.face.findPlane(self.tol):
            u0, u1, v0, v1 = self.bounds
            p1 = self.face.valueAt(u0, v0)
            p2 = self.face.valueAt(u1, v0)
            p3 = self.face.valueAt(u0, v1)
            return Part.Plane(p1, p2, p3)

    def get_cylinder(self, axis):
        cyl = Part.Cylinder()
        cyl.Axis = axis.Direction
        cyl.Center = axis.Location
        pt = self.face.valueAt(self.bounds[0], self.bounds[2])
        cyl.Radius = pt.distanceToLine(axis.Location, axis.Direction)
        return cyl

    def get_cone(self, apex, axis):
        cone = Part.Cone()
        cone.Axis = axis.Direction
        semiangle, center, radius = self.cone_data(apex, axis)
        cone.Center = center
        cone.Radius = radius
        cone.SemiAngle = semiangle
        return cone

    def fix_rotation(self, surf):
        "Rotate surface so that the seam is outside of the bounds"
        vec2 = FreeCAD.Base.Vector2d
        u0, u1, v0, v1 = self.bounds
        print(f"Face U range : {u0}, {u1}")
        l2do = Part.Geom2d.Line2dSegment(vec2(u0, v0), vec2(u1, v1))
        diago = l2do.toShape(self.face.Surface)
        u_width = u1 - u0

        pt1 = self.face.valueAt(u0, v0)
        pt2 = self.face.valueAt(u1, v1)
        s0, t0 = surf.parameter(pt1)
        s1, t1 = surf.parameter(pt2)
        l2dn = Part.Geom2d.Line2dSegment(vec2(s0, t0), vec2(s1, t1))
        diagn = l2dn.toShape(surf)

        if abs(diagn.Length - diago.Length) > self.tol:
            print(f"Diagonal error : {diagn.Length} != {diago.Length}")

        print(f"Surface S range : {s0}, {s1}")
        s_width = abs(s1 - s0)
        # print(s0, s1)
        if abs(u_width - s_width) > self.tol:
            print("Rotating")
            plm = FreeCAD.Placement()
            plm.rotate(surf.Center, surf.Axis, u1 - s0)
            surf.transform(plm.Matrix)
            # pt1 = self.face.valueAt(u0, v0)
            # pt2 = self.face.valueAt(u1, v1)
            s0, t0 = surf.parameter(pt1)
            s1, t1 = surf.parameter(pt2)
            print(f"Surface S range : {s0}, {s1}")
        return surf

    def get_surface(self):
        "Search and return canonical surface"
        if self.is_canonical():
            return self.face.Surface
        pl = self.get_plane()
        if pl:
            self.log("Surface is a plane")
            return pl
        sph = self.get_sphere()
        if sph:
            self.log("Surface is a sphere")
            return sph
        axis = planes_intersection(self.sample_planes(), self.tol)
        apex = lines_intersection(self.sample_lines(), self.tol)
        if isinstance(axis, Part.Line):
            axis = self.fix_axis_orientation(axis)
            if apex:
                self.log("Surface is a cone")
                cone = self.get_cone(apex, axis)
                return self.fix_rotation(cone)
            self.log("Surface is a cylinder")
            cyl = self.get_cylinder(axis)
            return self.fix_rotation(cyl)
        if axis:
            self.log("Surface is an extrusion")
            return None
        self.log("Surface is not canonical")


# *** Test Script ***

import FreeCADGui
m = 0.0
sel = FreeCADGui.Selection.getSelection()
for o in sel:
    FreeCAD.Console.PrintMessage(f"--- {o.Label} analysis\n")
    for i, face in enumerate(o.Shape.Faces):
        FreeCAD.Console.PrintMessage(f"Face{i + 1} ({face.Surface.TypeId})\n")
        sr = SurfaceIdentifier(face)
        # sr.bounds = face.ParameterRange
        surf = sr.get_surface()
        if surf:
            sr.report()
            u0, u1, v0, v1 = face.ParameterRange
            p1 = face.valueAt(u0, v0)
            p2 = face.valueAt(u1, v1)
            u0, v0 = surf.parameter(p1)
            u1, v1 = surf.parameter(p2)
            if u1 < u0:
                u0, u1 = u1, u0
            if v1 < v0:
                v0, v1 = v1, v0
            rts = Part.RectangularTrimmedSurface(surf, u0 - m, u1 + m, v0 - m, v1 + m)
            Part.show(rts.toShape(), f"Face{i + 1}")

        # for pl in sr.sample_planes():
        #     rts = Part.RectangularTrimmedSurface(pl, -100, 100, -100, 100)
        #     Part.show(rts.toShape())

"""
from importlib import reload
from freecad.Curves.lib import surface_identifier
reload(surface_identifier)
"""




