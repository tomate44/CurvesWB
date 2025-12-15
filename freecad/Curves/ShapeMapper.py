# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
import functools
import time


mes = FreeCAD.Console.PrintMessage


def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        mes(f"{func.__name__} took {elapsed_time:0.4f} seconds")
        return value
    return wrapper_timer


class BoundarySorter:
    """
    Sort a wire list to build faces
    Returns a list of lists of wires.
    Each returned list has an outerwire
    with eventually some inner wires.
    All input wires are supposed to be coplanar.
    """

    def __init__(self, wires):
        self.closed_wires = []
        self.parents = []
        self.sorted_wires = []
        self.open_wires = []
        # self.surface = surface
        for w in wires:
            if not w.isClosed():
                self.open_wires.append(w)
            else:
                self.closed_wires.append(w)
                self.parents.append([])
                self.sorted_wires.append([])
        self.done = False

    def check_inside(self):
        for i, w1 in enumerate(self.closed_wires):
            for j, w2 in enumerate(self.closed_wires):
                if not i == j:
                    if w2.BoundBox.isInside(w1.BoundBox):
                        # if self.fine_check_inside(w1, w2):
                        self.parents[i].append(j)

    def sort_pass(self):
        to_remove = []
        for i, p in enumerate(self.parents):
            if (p is not None) and p == []:
                to_remove.append(i)
                self.sorted_wires[i].append(self.closed_wires[i])
                self.parents[i] = None
        for i, p in enumerate(self.parents):
            if (p is not None) and len(p) == 1:
                to_remove.append(i)
                self.sorted_wires[p[0]].append(self.closed_wires[i])
                self.parents[i] = None
        # print("Removing full : {}".format(to_remove))
        if len(to_remove) > 0:
            for i, p in enumerate(self.parents):
                if (p is not None):
                    for r in to_remove:
                        if r in p:
                            p.remove(r)
        else:
            self.done = True

    def sort(self):
        self.check_inside()
        # print(self.parents)
        while not self.done:
            # print("Pass {}".format(i))
            self.sort_pass()
        result = []
        for w in self.sorted_wires:
            if w:
                result.append(w)
        self.sorted_wires = result


def validated_face(w, surf=None):
    ''' Attempt to create valid surface by increasing tolerance if required
    up to maxtol. On failure return a null face
    '''
    maxtol = 1e-4
    tol = w.getTolerance(1)
    while tol < maxtol:
        if surf is not None:
            f = Part.Face(surf, w)
        else:
            f = Part.Face(w)
        try:
            f.validate()
            break
        except Part.OCCError:
            tol *= 2
            w.fixTolerance(tol)
    if tol < maxtol:
        return f
    else:
        print('Face validation failed')
        return Part.Face()  # null face


def build_face(surf, wl, tol=1e-7):
    f = validated_face(wl[0], surf)  # should be valid or null...
    try:
        f.check()
    except Exception as e:
        print(str(e))
    if not f.isValid():
        print("Invalid initial face")
        f.validate()
    if len(wl) > 1:
        try:
            f.cutHoles(wl[1:])
            f.validate()
        except AttributeError:
            print("Faces with holes require FC 0.19+\nIgnoring holes\n")
        except Part.OCCError:
            print("Unable to cut hole in face")
    # f.sewShape()
    # f.check(True)
    # print_tolerance(f)
    if not f.isValid():
        print("Invalid final face")
    return f


def build_periodic_face(surf, wl, tol=1e-7):
    ffix = Part.ShapeFix.Face(surf, tol)
    for w in wl:
        ffix.add(w)
    ffix.perform()
    if ffix.fixOrientation():
        print("fixOrientation")
    if ffix.fixMissingSeam():
        print("fixMissingSeam")
    return ffix.face()

# --- Sort PCurves ---
# Algo may not be very efficient
# It may be better to port Part.sortEdges algo
# See AppPartPy @ 2188 and 158


def sq_dist(v1, v2):
    "return square distance between vectors or vectors2d"
    if isinstance(v1, FreeCAD.Vector):
        return (v1.x - v2.x)**2 + (v1.y - v2.y)**2 + (v1.z - v2.z)**2
    elif isinstance(v1, FreeCAD.Base.Vector2d):
        return (v1.x - v2.x)**2 + (v1.y - v2.y)**2


def contact(pc1, pc2, tol=1e-7):
    c1, fp1, lp1 = pc1
    c2, fp2, lp2 = pc2
    v1 = c1.value(fp1)
    v2 = c1.value(lp1)
    v3 = c2.value(fp2)
    v4 = c2.value(lp2)
    if sq_dist(v1, v3) < tol:
        # print("contact v1 v3")
        return True
    elif sq_dist(v1, v4) < tol:
        # print("contact v1 v4")
        return True
    elif sq_dist(v2, v3) < tol:
        # print("contact v2 v3")
        return True
    elif sq_dist(v2, v4) < tol:
        # print("contact v2 v4")
        return True
    # print("No contact")
    return False


# @timer
def find_joined_pcurves(pcurves, tol=1e-7):
    """Sort a list of pcurves
    and return a list of lists of joined pcurves
    """
    joined = []
    curr = [0]
    remain = list(range(1, len(pcurves)))
    while len(remain) > 0:
        # print(f"--- Search pass for {curr}")
        # print(remain)
        found = False
        for idx in remain:
            if contact(pcurves[curr[-1]], pcurves[idx]):
                curr.append(idx)
                remain.remove(idx)
                found = True
                # print(f"Found {idx}")
                break
        if not found:
            joined.append(curr)
            curr = [remain[0]]
            remain.pop(0)
    # if len(curr) == 1:
    joined.append(curr)
    # print(joined)
    return joined


def ruled_surfaces(shape1, shape2):
    "return ruled surfaces between shape1 and shape2"
    ruled = []
    if shape1.Faces:
        for h in range(len(shape1.Faces)):
            face_1 = shape1.Faces[h]
            face_2 = shape2.Faces[h]
            for i in range(len(face_1.Wires)):
                for j in range(len(face_1.Wires[i].Edges)):
                    if not face_1.Wires[i].Edges[j].isSeam(face_1):
                        rs = Part.makeRuledSurface(face_1.Wires[i].Edges[j],
                                                   face_2.Wires[i].Edges[j], 1)
                        # print(rs)
                        ruled.extend(rs.Faces)
    elif shape1.Wires:
        for i in range(len(shape1.Wires)):
            rs = Part.makeRuledSurface(shape1.Wires[i], shape2.Wires[i], 1)
            # print(rs)
            ruled.append(rs)
    else:
        for i in range(len(shape1.Edges)):
            rs = Part.makeRuledSurface(shape1.Edges[i], shape2.Edges[i], 1)
            ruled.append(rs)
    return Part.Compound(ruled)


def upgrade_faces(shape):
    "Try to upgrade a shape faces to a shell and solid"
    try:
        shell = Part.Shell(shape.Faces)
        if shell.isValid():
            shape = shell
    except Part.OCCError:
        print("Shell not valid")
    try:
        solid = Part.Solid(shape)
        if solid.isValid():
            shape = solid
    except Part.OCCError:
        print("Solid not valid")
    return shape


def grid(bounds=[0, 1, 0, 1], nbU=10, nbV=10, surface=None):
    """Create a grid of lines in specified range
    If surface is None :
    - Return 2 lists of (NbU + 1) and (NbV + 1) Line2dSegment
    Else :
    - Return 2 lists of (NbU + 1) and (NbV + 1) edges"""
    u0, u1, v0, v1 = bounds
    uiso = []
    for i in range(nbU + 1):
        u = u0 + i * (u1 - u0) / nbU
        p1 = FreeCAD.Base.Vector2d(u, v0)
        p2 = FreeCAD.Base.Vector2d(u, v1)
        line = Part.Geom2d.Line2dSegment(p1, p2)
        fp = line.FirstParameter
        lp = line.LastParameter
        if surface is None:
            uiso.append(line)
        else:
            uiso.append(line.toShape(surface, fp, lp))
    viso = []
    for i in range(nbV + 1):
        v = v0 + i * (v1 - v0) / nbV
        p1 = FreeCAD.Base.Vector2d(u0, v)
        p2 = FreeCAD.Base.Vector2d(u1, v)
        line = Part.Geom2d.Line2dSegment(p1, p2)
        fp = line.FirstParameter
        lp = line.LastParameter
        if surface is None:
            viso.append(line)
        else:
            viso.append(line.toShape(surface, fp, lp))
    return uiso, viso


def reverse_knots(knots):
    rev = []
    for k in knots[::-1]:
        rev.append(knots[-1] - (k - knots[0]))
    return rev


class ReversibleSurface:
    """BSpline surface that can be reversed in U and V direction
    Or that can have U and V directions swapped"""

    def __init__(self, surf):
        self.surface = surf

    @property
    def Face(self):
        return self.surface.toShape()

    @property
    def Surface(self):
        return self.surface

    def reverseU(self):
        revpoles = self.surface.getPoles()[::-1]
        for i, row in enumerate(revpoles):
            self.surface.setPoleRow(i + 1, row)
        self.surface.setUKnots(reverse_knots(self.surface.getUKnots()))

    def reverseV(self):
        poles = self.surface.getPoles()
        for i, row in enumerate(poles):
            self.surface.setPoleRow(i + 1, row[::-1])
        self.surface.setVKnots(reverse_knots(self.surface.getVKnots()))

    def swapUV(self):
        self.surface.exchangeUV()
        u0 = self.surface.getUKnot(1)
        u1 = self.surface.getUKnot(self.surface.NbUKnots)
        v0 = self.surface.getVKnot(1)
        v1 = self.surface.getVKnot(self.surface.NbVKnots)
        self.surface.scaleKnotsToBounds(v0, v1, u0, u1)

    def is_bilinear(self):
        matchdeg = (self.surface.UDegree == 1) and (self.surface.VDegree == 1)
        matchpol = (self.surface.NbUPoles == 2) and (self.surface.NbVPoles == 2)
        return matchdeg and matchpol

    def get_center(self):
        u0, u1, v0, v1 = self.surface.bounds()
        iso0 = self.surface.uIso(u0)
        iso1 = self.surface.uIso(0.75 * u0 + 0.25 * u1)
        iso2 = self.surface.uIso(0.25 * u0 + 0.75 * u1)
        i1 = iso0.intersect(iso1)
        i2 = iso0.intersect(iso2)
        if (len(i1) > 0) and (len(i2) > 0):
            p1 = FreeCAD.Vector(i1[0].X, i1[0].Y, i1[0].Z)
            p2 = FreeCAD.Vector(i2[0].X, i2[0].Y, i2[0].Z)
            if p1.distanceToPoint(p2) < 1e-7:
                return p1

    def extend(self, *args):
        FreeCAD.Console.PrintError("Extending surface not implemented\n")


class TransferSurface(ReversibleSurface):
    def __init__(self, surf):
        super(TransferSurface, self).__init__(surf)
        if isinstance(surf, Part.Face):
            s0, s1, t0, t1 = surf.ParameterRange
            rts = Part.RectangularTrimmedSurface(surf.Surface, s0, s1, t0, t1)
            self.surface = rts.toBSpline()
        else:
            self.surface = surf.toBSpline()


class Quad(ReversibleSurface):
    def __init__(self, geomrange=[0, 1, 0, 1], paramrange=[0, 1, 0, 1]):
        super(Quad, self).__init__(Part.BSplineSurface())
        self.GeometryRange = geomrange
        self.ParameterRange = paramrange

    @property
    def GeometryRange(self):
        pu1, pu2 = self.surface.getPoles()
        p00 = pu1[0]
        p11 = pu2[-1]
        return p00.x, p11.x, p00.y, p11.y

    @GeometryRange.setter
    def GeometryRange(self, bounds):
        if not (len(bounds) == 4):
            raise RuntimeError("Quad need 4 bounds")
        u0, u1, v0, v1 = bounds
        self.surface.setPole(1, 1, FreeCAD.Vector(u0, v0, 0))
        self.surface.setPole(1, 2, FreeCAD.Vector(u0, v1, 0))
        self.surface.setPole(2, 1, FreeCAD.Vector(u1, v0, 0))
        self.surface.setPole(2, 2, FreeCAD.Vector(u1, v1, 0))

    @property
    def ParameterRange(self):
        return self.surface.bounds()

    @ParameterRange.setter
    def ParameterRange(self, bounds):
        if not (len(bounds) == 4):
            raise RuntimeError("Quad need 4 bounds")
        # print(bounds)
        self.surface.setUKnots(bounds[:2])
        # self.surface.setUKnot(2, bounds[1])
        self.surface.setVKnots(bounds[2:])
        # self.surface.setVKnot(2, bounds[3])
        # self.surface.scaleKnotsToBounds(*bounds) is less precise

    # def extend_by_value(self, bounds):
    #     u0, u1, v0, v1 = self.GeometryRange
    #     if len(bounds) == 1:
    #         margins = bounds * 4
    #     elif len(bounds) == 2:
    #         margins = bounds[:1] * 2 + bounds[1:] * 2
    #     elif len(bounds) == 4:
    #         margins = bounds
    #     else:
    #         raise RuntimeError("Quad.extend_by_value need 1,2 or 4 parameters")
    #     s0 = u0 - margins[0]
    #     s1 = u1 + margins[1]
    #     t0 = v0 - margins[2]
    #     t1 = v1 + margins[3]
    #     self.extend(s0, s1, t0, t1)

    def get_new_geom_bounds(self, numU, numV):
        u0, u1, v0, v1 = self.GeometryRange
        eu = (u1 - u0) * numU
        ev = (v1 - v0) * numV
        s0 = u0 - eu
        s1 = u1 + eu
        t0 = v0 - ev
        t1 = v1 + ev
        return (s0, s1, t0, t1)

    def extend(self, numU=1, numV=1):
        u0, u1, v0, v1 = self.GeometryRange
        s0, s1, t0, t1 = self.get_new_geom_bounds(numU, numV)
        ku0, ku1, kv0, kv1 = self.ParameterRange
        nu0, nu1, nv0, nv1 = self.ParameterRange
        if s0 < u0:
            nu0 += (ku1 - ku0) * (s0 - u0) / (u1 - u0)
        if s1 > u1:
            nu1 += (ku1 - ku0) * (s1 - u1) / (u1 - u0)
        if t0 < v0:
            nv0 += (kv1 - kv0) * (t0 - v0) / (v1 - v0)
        if t1 > v1:
            nv1 += (kv1 - kv0) * (t1 - v1) / (v1 - v0)
        self.GeometryRange = s0, s1, t0, t1
        self.ParameterRange = nu0, nu1, nv0, nv1


class ShapeMapper:
    """
    Map shapes on a target face
    """

    def __init__(self, source, target, transfer=None):
        self.Source = source
        self.Target = target
        self.Transfer = transfer
        self._flat_wires = None
        self._sorted_wires = None
        self.Tolerance = 1e-7
        self.Messages = ["", ]
        _ = self.FlatWires
        # _ = self.SortedWires

    def timer(func):
        def wrapper_timer(self, *args, **kwargs):
            tic = time.perf_counter()
            value = func(self, *args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            self.Messages.append(f"{func.__name__}: {elapsed_time:0.4f} seconds")
            return value
        return wrapper_timer

    @property
    def FlatWires(self):
        if self._flat_wires is None:
            self._flat_wires = self.get_flat_wires()
        return self._flat_wires

    @property
    def SortedWires(self):
        if self._sorted_wires is None:
            self._sorted_wires = self.sort_wires()
        return self._sorted_wires

    @timer
    def get_pcurves(self):
        "Returns a list of pcurves from the Source shape edges"
        pcurves = []
        if self.Transfer is None and hasattr(self.Source, "Surface"):
            for e in self.Source.Edges:
                pcurve, fp, lp = self.Source.curveOnSurface(e)
                if e.Orientation == "Reversed":
                    pcurve.reverse()
                pcurves.append((pcurve, fp, lp))
        elif hasattr(self.Transfer, "Surface"):  # self.Transfer is a face
            proj = self.Transfer.project([self.Source])
            for e in proj.Edges:
                pcurve, fp, lp = self.Transfer.curveOnSurface(e)
                if e.Orientation == "Reversed":
                    pcurve.reverse()
                pcurves.append((pcurve, fp, lp))
        return pcurves

    @timer
    def get_flat_wires(self):
        "Returns a list of flat wires (on XY plane) from joined pcurves"
        pc = self.get_pcurves()
        # print(pc)
        se = find_joined_pcurves(pc)
        wires = []
        pl = Part.Plane()
        for el in se:
            edges = [pc[i][0].toShape(pl, pc[i][1], pc[i][2]) for i in el]
            try:
                w = Part.Wire(edges)
            except Part.OCCError:
                Part.show(Part.Compound(edges))
            fix = Part.ShapeFix.Wire()
            fix.load(w)
            fix.perform()
            wires.append(fix.wire())
        return wires

    @timer
    def sort_wires(self):
        """Sort wires in order to build faces
        and returns two lists :
        - closed wires is a list of lists of wires
        - open wires is a list
        """
        # bs = BoundarySorter(self.FlatWires)
        # bs.sort()
        # return bs.sorted_wires, bs.open_wires

        sorter = BoundarySorter(self.FlatWires)
        sorter.sort()
        return sorter.sorted_wires, sorter.open_wires

    def map_edge_on_surface(self, edge, surface):
        """Maps an edge's first pcurve on a surface.
        Returns an edge
        """
        pcurve = edge.curveOnSurface(0)
        if pcurve:
            return pcurve[0].toShape(surface, pcurve[3], pcurve[4])

    # @timer
    def map_on_surface(self, wires, surface, fill=False):
        """Maps a list of wires on a surface.
        Returns a compound of wires if fill = False
        or a face if fill = True
        """
        wl = []
        ori = "Forward"
        for w in wires:
            el = []
            for e in w.Edges:
                me = self.map_edge_on_surface(e, surface)
                if me:
                    el.append(me)
            nw = Part.Wire(el)
            nw.Orientation = ori
            ori = "Reversed"
            wl.append(nw)
        if not fill:
            return Part.Compound(wl)
        face = build_face(surface, wl, self.Tolerance)
        return face

    def offset_face(self, face, offset):
        if offset == 0.0:
            return face
        if face.Surface.Continuity == 'C0':
            # TODO : create a C1 approximation
            raise (RuntimeError, "Surface must be at least C1 continuous")
        return face.makeOffsetShape(offset, self.Tolerance).Face1

    @timer
    def get_shapes(self, offset=0.0, fillfaces=True):
        off1 = self.offset_face(self.Target, offset).Face1
        if not fillfaces:
            sh1 = self.map_on_surface(self.FlatWires, off1.Surface, False)
            return Part.Compound(), sh1  # Compound of wires
        # fillfaces = True
        face_wires, other_wires = self.SortedWires
        faces = []
        for wl in face_wires:
            face_1 = self.map_on_surface(wl, off1.Surface, True)
            faces.append(face_1)

        openwl1 = self.map_on_surface(other_wires, off1.Surface, False).Wires
        open_wires = []
        closed_wires = []
        for w in openwl1:
            if w.isClosed():
                closed_wires.append(w)
            else:
                open_wires.append(w)

        # TODO : sort wires along the seam
        n = int(len(closed_wires) / 2)
        for j in range(n):
            i = j * 2
            # print(i)
            face_1 = build_periodic_face(off1.Surface, closed_wires[i:i + 2])
            faces.append(face_1)

        wl = sh1 = self.map_on_surface(open_wires, off1.Surface, False)
        return Part.Compound(faces), wl

    @timer
    def get_extrusion(self, offset1=0.0, offset2=1.0):
        _, wires1 = self.get_shapes(offset1, False)
        _, wires2 = self.get_shapes(offset2, False)
        shells = []
        for i in range(len(wires1.Wires)):
            faces = []
            for j in range(len(wires1.Wires[i].Edges)):
                ruled = ruled_surfaces(wires1.Wires[i].Edges[j],
                                       wires2.Wires[i].Edges[j])
                faces.extend(ruled.Faces)
            shells.append(Part.Shell(faces))
        return Part.Compound(shells)

    @timer
    def get_solids(self, offset1=0.0, offset2=1.0):
        faces_1, _ = self.get_shapes(offset1, True)
        faces_2, _ = self.get_shapes(offset2, True)
        solids = []
        for i in range(len(faces_1.Faces)):
            f1 = faces_1.Faces[i]
            f2 = faces_2.Faces[i]
            ruled = ruled_surfaces(f1, f2)
            ruled.add(f1)
            ruled.add(f2)
            so = upgrade_faces(ruled)
            solids.append(so)
        return Part.Compound(solids)


@timer
def test():
    sel = FreeCADGui.Selection.getSelectionEx()
    source = sel[0].Object.Shape
    target = sel[1].SubObjects[0]
    if len(sel) > 2:
        transfer = sel[2].SubObjects[0]
    else:
        transfer = None

    print(f"Source : {source}")
    print(f"Target : {target}")
    print(f"Transfer : {transfer}")

    sm = ShapeMapper(source, target, transfer)
    # print(sm.get_pcurves())
    # print(sm.get_flat_wires())
    # closed, openwl = sm.sort_wires()
    # face = sm.map_on_surface(closed[0], target.Surface, True)
    # Part.show(face)
    # face.check(True)
    grid1 = grid(bounds=target.ParameterRange, nbU=10, nbV=10, surface=target.Surface)
    grsh1 = Part.Compound(grid1[0] + grid1[1])
    Part.show(grsh1, "GridOnTarget")
    print("GridOnTarget")
    if transfer:
        surf = transfer.Surface
    else:
        surf = Part.Plane()
    grid2 = grid(bounds=target.ParameterRange, nbU=10, nbV=10, surface=surf)
    grsh2 = Part.Compound(grid2[0] + grid2[1])
    Part.show(grsh2, "GridOnTransfer")
    print("GridOnTransfer")
    shells = sm.get_extrusion(0.0, 1.0)
    Part.show(shells, "extrusion")
    print("extrusion")
    faces, _ = sm.get_shapes(2.0)
    Part.show(faces, "faces")
    print("faces")
    solids = sm.get_solids(-0.1, 0.5)
    Part.show(solids, "solids")
    print("solids")


# test()
