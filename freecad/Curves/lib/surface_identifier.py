import FreeCAD
import Part
from random import random
from math import pi


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

    def mean_vec(self, vectors):
        "Return the mean of a list of vectors"
        point = FreeCAD.Vector()
        for pt in vectors:
            point += pt
        point /= len(vectors)
        return point

    def mean_line(self, lines):
        "Return the mean of a list of lines"
        direction = self.mean_vec([li.Direction for li in lines])
        location = self.mean_vec([li.Location for li in lines])
        return Part.Line(location, direction)

    def uniform_UV(self):
        "Uniform generator of (u, v) parameters in the source face bounds"
        i = 0
        u0, u1, v0, v1 = self.bounds
        urange = u1 - u0
        vrange = v1 - v0
        n = int(pow(self.num_samples, 0.5))
        for i in range(n):
            u = u0 + i * urange / (n - 1)
            for j in range(n):
                v = v0 + j * vrange / (n - 1)
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

    def find_sphere(self):
        lines = []
        for u, v in self.uniform_UV():
            p1 = self.face.valueAt(u, v)
            n = self.face.normalAt(u, v)
            li = Part.Line(p1, p1 + n)
            lines.append(li)
        center = self.find_apex(lines)
        if center is None:
            return
        pt = self.face.valueAt(self.bounds[0], self.bounds[2])
        radius = pt.distanceToPoint(center)
        sph = Part.Sphere()
        sph.Center = center
        sph.Radius = radius
        return sph

    def find_apex(self, lines=None):
        """
        If lines all intersect into one point.
        Returns this point, or None otherwise.
        """
        size = 1e6
        if lines is None:
            lines = self.sample_lines()
        interlist = []
        for i in range(len(lines) - 1):
            li1 = lines[i].toShape(-size, size)
            li2 = lines[i + 1].toShape(-size, size)
            d, pts, info = li1.distToShape(li2)
            if d > self.tol:
                # self.log(f"Find_apex, intersection #{i} : {d} out of tolerance {self.tol}")
                return None
            interlist.append(0.5 * pts[0][0] + 0.5 * pts[0][1])
        for i in range(len(interlist) - 1):
            d = interlist[i].distanceToPoint(interlist[i + 1])
            if d > self.tol:
                # self.log(f"Find_apex, intersection #{i} : {d} out of tolerance {self.tol}")
                return None
        self.Apex = self.mean_vec(interlist)
        self.log(f"Found Apex {self.vecstr(self.Apex)}")
        return self.Apex

    def find_axis(self, planes=None):
        """
        If planes all intersect into one line, return this line.
        If planes intersect into parallel lines, return the direction.
        Else, return None
        """
        if planes is None:
            planes = self.sample_planes()
        interlist = []
        for i in range(len(planes) - 1):
            inter = planes[i].intersect(planes[i + 1])
            # print(inter)
            interlist.extend(inter)
        if len(interlist) == 0:
            return None
        # Part.show(Part.Compound([il.toShape(-100, 100) for il in interlist]))
        coincident = True
        for i in range(len(interlist) - 1):
            i1 = interlist[i]
            i2 = interlist[i + 1]
            dotprod = i1.Direction.dot(i2.Direction)
            if (1.0 - abs(dotprod)) > self.tol:
                # print(f"plane intersection #{i}: out of tolerance {self.tol}")
                return None
            if dotprod < 0:
                i2.reverse()
            if i1.Location.distanceToLine(i2.Location, i2.Direction) > self.tol:
                coincident = False
        if coincident:
            self.Center = self.mean_vec([li.Location for li in interlist])
            self.log(f"Found Center {self.vecstr(self.Center)}")
        self.Axis = self.mean_vec([li.Direction for li in interlist])
        self.log(f"Found Axis {self.vecstr(self.Axis)}")
        return self.Axis

    def cone_data(self):
        "Compute semi-angle, center and radius of a cone"
        axis_line = Part.Line(self.Apex, self.Apex + self.Axis)
        pt1 = self.face.valueAt(self.bounds[0], self.bounds[2])
        pt2 = self.face.valueAt(self.bounds[1], self.bounds[3])
        proj1 = axis_line.projectPoint(pt1)
        proj2 = axis_line.projectPoint(pt2)
        par1 = axis_line.parameter(proj1)
        par2 = axis_line.parameter(proj2)
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

    def cylinder_radius(self):
        "Returns the radius of a surface with axis, and no apex"
        pt = self.face.valueAt(u0, v0)
        self.Radius = pt.distanceToLine(self.Center, self.Axis)
        return self.Radius

    def find_plane(self):
        return self.face.findPlane(self.tol)

    def is_canonical(self):
        types = ('Part::GeomPlane',
                 'Part::GeomCylinder',
                 'Part::GeomCone',
                 'Part::GeomSphere'
                 'Part::GeomToroid')
        if self.face.Surface.TypeId in types:
            return True
        return False

    def get_cylinder(self):
        cyl = Part.Cylinder()
        cyl.Axis = self.Axis
        cyl.Center = self.Center
        cyl.Radius = self.cylinder_radius()
        return cyl

    def get_cone(self):
        cone = Part.Cone()
        cone.Axis = self.Axis
        semiangle, center, radius = self.cone_data()
        cone.Center = center
        cone.Radius = radius
        cone.SemiAngle = semiangle
        return cone

    def analyze(self):
        if self.is_canonical():
            return None
        sph = self.find_sphere()
        if sph:
            self.log("Surface is a sphere")
            return sph
        pl = self.find_plane()
        if pl:
            self.log("Surface is a plane")
            return pl
        axis = self.find_axis()
        if axis and self.Center:
            self.log("Surface is a cylinder")
            return self.get_cylinder()
        apex = self.find_apex()
        if axis and apex:
            self.log("Surface is a cone")
            return self.get_cone()
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
        surf = sr.analyze()
        if surf:
            sr.report()
            u0, u1, v0, v1 = face.ParameterRange
            p1 = face.valueAt(u0, v0)
            p2 = face.valueAt(u1, v1)
            u0, v0 = surf.parameter(p1)
            u1, v1 = surf.parameter(p2)
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




