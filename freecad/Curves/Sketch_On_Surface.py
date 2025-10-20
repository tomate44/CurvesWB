# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Sketch on surface"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Map a sketch on a surface"

import os
import FreeCAD
import FreeCADGui
import Part
import Sketcher
from freecad.Curves import _utils
from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, 'sketch_surf.svg')

debug = _utils.debug
# debug = _utils.doNothing
vec = FreeCAD.Vector
error = FreeCAD.Console.PrintError


def ruled_surface(sh1, sh2):
    try:
        return Part.makeRuledSurface(path=sh1, profile=sh2, orientation=1)
    except TypeError:
        return Part.makeRuledSurface(sh1, sh2)


def stretched_plane(poles, param_range=[0, 2, 0, 2], extend_factor=1.0):
    s0, s1, t0, t1 = param_range
    bs = Part.BSplineSurface()
    umults = [2, 2]
    vmults = [2, 2]
    uknots = [s0, s1]
    vknots = [t0, t1]
    if extend_factor > 1.0:
        ur = s1 - s0
        vr = t1 - t0
        uknots = [s0 - extend_factor * ur, s1 + extend_factor * ur]
        vknots = [t0 - extend_factor * vr, t1 + extend_factor * vr]
        diag_1 = poles[1][1] - poles[0][0]
        diag_2 = poles[1][0] - poles[0][1]
        np1 = poles[0][0] - extend_factor * diag_1
        np2 = poles[0][1] - extend_factor * diag_2
        np3 = poles[1][0] + extend_factor * diag_2
        np4 = poles[1][1] + extend_factor * diag_1
        poles = [[np1, np2], [np3, np4]]
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                False, False, 1, 1)
    return bs

def validated_face(w, surf=None):
    ''' Attempt to create valid surface by increasing tolerance if required up to
    maxtol. On failure return a null face
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
        debug('Face validation failed')
        return Part.Face()  #null face


class BoundarySorter:
    def __init__(self, wires, surface=None, only_closed=False):
        self.wires = []
        self.parents = []
        self.sorted_wires = []
        self.surface = surface
        for w in wires:
            if only_closed and not w.isClosed():
                debug("Skipping open wire")
                continue
            self.wires.append(w)
            self.parents.append([])
            self.sorted_wires.append([])
        self.done = False

    def fine_check_inside(self, w1, w2):
        f = validated_face(w2, self.surface)
        if f.isNull():
            return False
        if f.isValid():
            pt = w1.Vertex1.Point
            u, v = f.Surface.parameter(pt)
            return f.isPartOfDomain(u, v)
        return False

    def check_inside(self):
        for i, w1 in enumerate(self.wires):
            for j, w2 in enumerate(self.wires):
                if not i == j:
                    if w2.BoundBox.isInside(w1.BoundBox):
                        if self.fine_check_inside(w1, w2):
                            self.parents[i].append(j)

    def sort_pass(self):
        to_remove = []
        for i, p in enumerate(self.parents):
            if (p is not None) and p == []:
                to_remove.append(i)
                self.sorted_wires[i].append(self.wires[i])
                self.parents[i] = None
        for i, p in enumerate(self.parents):
            if (p is not None) and len(p) == 1:
                to_remove.append(i)
                self.sorted_wires[p[0]].append(self.wires[i])
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
        return result


def tolerance_msg(shape, ty):
    a = shape.getTolerance(-1, ty)
    b = shape.getTolerance(0, ty)
    c = shape.getTolerance(1, ty)
    print("{0} : {1:.2e} / {2:.2e} / {3:.2e}".format(ty, a, b, c))


def print_tolerance(shape):
    if shape.Faces:
        tolerance_msg(shape, Part.Face)
    if shape.Edges:
        tolerance_msg(shape, Part.Edge)
    if shape.Vertexes:
        tolerance_msg(shape, Part.Vertex)


class sketchOnSurface:
    "This feature object maps a sketch on a surface"
    def __init__(self, obj):
        obj.addProperty("App::PropertyLink", "Sketch", "SketchOnSurface",
                        "Input Sketch")
        obj.addProperty("App::PropertyLinkList", "ExtraObjects",
                        "SketchOnSurface",
                        "Additional objects that will be mapped on surface")
        obj.addProperty("App::PropertyBool", "FillFaces", "Settings",
                        "Make faces from closed wires").FillFaces = False
        obj.addProperty("App::PropertyBool", "FillExtrusion", "Settings",
                        "Add extrusion faces").FillExtrusion = True
        obj.addProperty("App::PropertyFloat", "Offset",   "Settings",
                        "Offset distance of mapped sketch").Offset = 0.0
        obj.addProperty("App::PropertyFloat", "Thickness", "Settings",
                        "Extrusion thickness").Thickness = 0.0
        obj.addProperty("App::PropertyBool", "ReverseU", "Touchup",
                        "Reverse U direction").ReverseU = False
        obj.addProperty("App::PropertyBool", "ReverseV", "Touchup",
                        "Reverse V direction").ReverseV = False
        obj.addProperty("App::PropertyBool", "SwapUV", "Touchup",
                        "Swap U and V directions").ReverseV = False
        obj.addProperty("App::PropertyBool", "ConstructionBounds", "Touchup",
                        "include construction geometry in sketch bounds").ConstructionBounds = True
        obj.Proxy = self

    def force_closed_bspline2d(self, c2d):
        """Force close a 2D Bspline curve by moving last pole to first"""
        c2d.setPole(c2d.NbPoles, c2d.getPole(1))
        debug("Force closing 2D curve")

    def build_faces(self, wl, face):
        faces = []
        for w in wl:
            w.fixWire(face, 1e-7)
        bs = BoundarySorter(wl, face.Surface, True)
        for i, wirelist in enumerate(bs.sort()):
            # print(wirelist)
            f = validated_face(wirelist[0], face.Surface) #should valid or null...
            try:
                f.check()
            except Exception as e:
                debug(str(e))
            if not f.isValid():
                debug("{:3}:Invalid initial face".format(i))
                f.validate()
            if len(wirelist) > 1:
                try:
                    f.cutHoles(wirelist[1:])
                    f.validate()
                except AttributeError:
                    error("Faces with holes require FC 0.19 or higher\nIgnoring holes\n")
                except Part.OCCError:
                    error("Unable to cut hole in face")
            # f.sewShape()
            # f.check(True)
            # print_tolerance(f)
            if not f.isValid():
                error("{:3}:Invalid final face".format(i))
            faces.append(f)
        return faces

    def map_shapelist(self, shapes, quad, face, fillfaces=False):
        shapelist = []
        for i, shape in enumerate(shapes):
            debug("mapping shape #  {}".format(i + 1))
            shapelist.extend(self.map_shape(shape, quad, face, fillfaces))
            debug("Total : {} shapes".format(len(shapelist)))
        return shapelist

    def map_shape(self, shape, quad, face, fillfaces=False):
        if not isinstance(shape, Part.Shape):
            return []
        # proj = quad.project(shape.Edges)
        new_edges = []
        for oe in shape.Edges:
            # debug("original edge has : {} Pcurves : {}".format(_utils.nb_pcurves(oe), oe.curveOnSurface(0)))
            proj = quad.project([oe])
            for e in proj.Edges:
                # debug("edge on quad has : {} Pcurves : {}".format(_utils.nb_pcurves(e), e.curveOnSurface(0)))
                c2d, fp, lp = quad.curveOnSurface(e)
                if oe.isClosed() and not c2d.isClosed():
                    self.force_closed_bspline2d(c2d)
                ne = c2d.toShape(face.Surface, fp, lp)
                # debug("edge on face has : {} Pcurves : {}".format(_utils.nb_pcurves(ne), ne.curveOnSurface(0)))
                # debug(ne.Placement)
                # debug(face.Placement)
                # ne.Placement = face.Placement
                vt = ne.getTolerance(1, Part.Vertex)
                et = ne.getTolerance(1, Part.Edge)
                if vt < et:
                    ne.fixTolerance(et, Part.Vertex)
                    # debug("fixing tolerance : {0:e} -> {1:e}".format(vt,et))
                new_edges.append(ne)
            # else: # except TypeError:
                # error("Failed to get 2D curve")
        sorted_edges = Part.sortEdges(new_edges)
        wirelist = [Part.Wire(el) for el in sorted_edges]
        if fillfaces:
            return self.build_faces(wirelist, face)
        else:
            return wirelist

    def offset_face(self, face, offset):
        """makeOffsetShape generates a plane from any planar surface.
        But we want to keep the parametric space of the original surface."""
        u0, u1, v0, v1 = face.ParameterRange
        if face.Surface.isPlanar():
            n = face.normalAt(u0, v0)
            nf = face.copy()
            nf.translate(n * offset)
            return nf
        if face.Orientation == "Reversed":
            offset = -offset
        offsurf = Part.OffsetSurface(face.Surface, offset)
        rts = Part.RectangularTrimmedSurface(offsurf, u0, u1, v0, v1)
        return rts.toShape()

    def execute(self, obj):
        if not obj.Sketch:
            error("No Sketch attached")
            return
        for i in range(len(obj.Sketch.Geometry)):
            try:
                obj.Sketch.deleteUnusedInternalGeometry(i)
            except ValueError:
                pass
        skedges = []
        for i in range(len(obj.Sketch.Geometry)):
            try:
                cons = obj.Sketch.Geometry[i].Construction
            except AttributeError:
                cons = obj.Sketch.getConstruction(i)
            if cons and not obj.ConstructionBounds:
                continue
            skedges.append(obj.Sketch.Geometry[i].toShape())
        comp = Part.Compound(skedges)

        bb = comp.BoundBox
        u0, u1, v0, v1 = (bb.XMin, bb.XMax, bb.YMin, bb.YMax)
        debug("Sketch bounds = {}".format((u0, u1, v0, v1)))
        try:
            if hasattr(obj.Sketch, "Support"):
                supp = obj.Sketch.Support
            if hasattr(obj.Sketch, "AttachmentSupport"):
                supp = obj.Sketch.AttachmentSupport
            n = eval(supp[0][1][0].lstrip('Face'))
            face = supp[0][0].Shape.Faces[n - 1]
            # face.Placement = obj.Sketch.Support[0][0].getGlobalPlacement()
        except (IndexError, AttributeError, SyntaxError) as e:
            error("{}\n".format(e))
            error("Failed to get the face support of the sketch\n")
            return
        debug("Target face bounds = {}".format(face.ParameterRange))
        prange = face.ParameterRange
        if obj.ReverseU:
            u0, u1 = u1, u0
        if obj.ReverseV:
            v0, v1 = v1, v0
        if obj.SwapUV:
            # u0, u1, v0, v1 = v0, v1, u0, u1
            prange = face.ParameterRange[2:] + face.ParameterRange[:2]
        pts = [[FreeCAD.Vector(u0, v0, 0), FreeCAD.Vector(u0, v1, 0)],
               [FreeCAD.Vector(u1, v0, 0), FreeCAD.Vector(u1, v1, 0)]]
        bs = stretched_plane(pts, prange, 1000.0)
        if obj.SwapUV:
            bs.exchangeUV()
        quad = bs.toShape()
        m = obj.Sketch.getGlobalPlacement().Matrix
        m.invert()
        inp_sh = [obj.Sketch.Shape.copy()] + [o.Shape.copy() for o in obj.ExtraObjects]
        input_shapes = []
        for sh in inp_sh:
            if not sh.isNull():
                sh.transformShape(m)
                input_shapes.append(sh)
        shapes_1 = []
        shapes_2 = []
        if (obj.Offset == 0):
            shapes_1 = self.map_shapelist(input_shapes, quad, face, obj.FillFaces)
        else:
            f1 = self.offset_face(face, obj.Offset)
            shapes_1 = self.map_shapelist(input_shapes, quad, f1.Face1, obj.FillFaces)
        if (obj.Thickness == 0):
            if shapes_1:
                obj.Shape = Part.Compound(shapes_1)
            return
        else:
            f2 = self.offset_face(face, obj.Offset + obj.Thickness)
            shapes_2 = self.map_shapelist(input_shapes, quad, f2.Face1, obj.FillFaces)
            if not obj.FillExtrusion:
                if shapes_1 or shapes_2:
                    obj.Shape = Part.Compound(shapes_1 + shapes_2)
                    return
            else:
                shapes = []
                for i in range(len(shapes_1)):
                    if not (len(shapes_1[i].Edges) == len(shapes_2[i].Edges)):
                        continue
                    if isinstance(shapes_1[i], Part.Face):
                        faces = shapes_1[i].Faces + shapes_2[i].Faces
                        for j in range(len(shapes_1[i].Edges)):
                            if obj.FillFaces and shapes_1[i].Edges[j].isSeam(shapes_1[i]):
                                continue
                            ruled = ruled_surface(shapes_1[i].Edges[j], shapes_2[i].Edges[j])
                            try:
                                ruled.check(False)
                            except ValueError:
                                continue
                            faces.append(ruled)
                            # try:
                                # face_is_closed = False
                                # for ed in shapes_1[i].Wires[j].Edges:
                                    # if ed.isSeam(shapes_1[i]):
                                        # face_is_closed = True
                                        # debug("closed face detected")
                                # loft = Part.makeLoft([shapes_1[i].Wires[j], shapes_2[i].Wires[j]], False, True, face_is_closed, 5)
                                # faces.extend(loft.Faces)
                            # except Part.OCCError:
                                # # error_wires.extend([shapes_1[i].Wires[j], shapes_2[i].Wires[j]])
                                # FreeCAD.Console.PrintError("Sketch on surface : failed to create loft face ({},{})".format(i,j))
                        try:
                            shell = Part.Shell(faces)
                            shell.sewShape()
                            # print_tolerance(shell)
                            solid = Part.Solid(shell)
                            solid.fixTolerance(1e-5)
                            shapes.append(solid)
                        except Exception:
                            FreeCAD.Console.PrintWarning("Sketch on surface : failed to create solid # {}.\n".format(i + 1))
                            shapes.extend(faces)
                    else:
                        ruled = ruled_surface(shapes_1[i].Wires[0], shapes_2[i].Wires[0])
                        try:
                            ruled.check(False)
                            shapes.append(ruled)
                        except ValueError:
                            pass
                # shapes.append(quad)
                if shapes:
                    if len(shapes) == 1:
                        obj.Shape = shapes[0]
                    elif len(shapes) > 1:
                        obj.Shape = Part.Compound(shapes)


class sosVP:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.children = []

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    if FreeCAD.Version()[0] == "0" and '.'.join(FreeCAD.Version()[1:3]) >= '21.2':
        def dumps(self):
            return {"name": self.Object.Name}

        def loads(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    else:
        def __getstate__(self):
            return {"name": self.Object.Name}

        def __setstate__(self, state):
            self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
            return None

    def claimChildren(self):
        return [self.Object.Sketch]


def addFaceWireToSketch(fa, w, sk):
    curves = list()
    const = list()
    pl = Part.Plane()
    for idx in range(len(w.Edges)):
        e, fp, lp = fa.curveOnSurface(w.Edges[idx])
        e3d = e.toShape(pl)
        tc = e3d.Curve.trim(fp, lp)
        curves.append(tc)
    o = int(sk.GeometryCount)
    sk.addGeometry(curves, False)
    for idx in range(len(curves)):
        const.append(Sketcher.Constraint('Block', o + idx))
    sk.addConstraint(const)


def addFaceBoundsToSketch(para_range, sk):
    geoList = list()
    conList = list()
    u0, u1, v0, v1 = para_range
    geoList.append(Part.LineSegment(vec(u0, v0, 0), vec(u1, v0, 0)))
    geoList.append(Part.LineSegment(vec(u1, v0, 0), vec(u1, v1, 0)))
    geoList.append(Part.LineSegment(vec(u1, v1, 0), vec(u0, v1, 0)))
    geoList.append(Part.LineSegment(vec(u0, v1, 0), vec(u0, v0, 0)))
    o = int(sk.GeometryCount)
    sk.addGeometry(geoList, False)

    conList.append(Sketcher.Constraint('Coincident', o + 0, 1, -1, 1))
    conList.append(Sketcher.Constraint('Coincident', o + 0, 2, o + 1, 1))
    conList.append(Sketcher.Constraint('Coincident', o + 1, 2, o + 2, 1))
    conList.append(Sketcher.Constraint('Coincident', o + 2, 2, o + 3, 1))
    conList.append(Sketcher.Constraint('Coincident', o + 3, 2, o + 0, 1))
    conList.append(Sketcher.Constraint('Horizontal', o + 0))
    conList.append(Sketcher.Constraint('Horizontal', o + 2))
    conList.append(Sketcher.Constraint('Vertical', o + 1))
    conList.append(Sketcher.Constraint('Vertical', o + 3))
    conList.append(Sketcher.Constraint('DistanceX', o + 2, 2, o + 2, 1, u1 - u0))
    conList.append(Sketcher.Constraint('DistanceY', o + 1, 1, o + 1, 2, v1 - v0))
    # conList.append(Sketcher.Constraint('DistanceX', o + 0, 1, -1, 1, -u0))
    # conList.append(Sketcher.Constraint('DistanceY', o + 0, 1, -1, 1, -v0))
    sk.addConstraint(conList)


def build_sketch(sk, fa):
    #  add the bounding box of the face to the sketch
    u0, u1, v0, v1 = fa.ParameterRange
    rts = Part.RectangularTrimmedSurface(fa.Surface, u0, u1, v0, v1)
    lu1 = rts.uIso(u0)
    lu2 = rts.uIso(0.5 * (u0 + u1))
    lu3 = rts.uIso(u1)
    lv1 = rts.vIso(v0)
    lv2 = rts.vIso(0.5 * (v0 + v1))
    lv3 = rts.vIso(v1)
    # bb = rts.toShape()
    u = max([lv1.length(), lv2.length(), lv3.length()])
    v = max([lu1.length(), lu2.length(), lu3.length()])
    addFaceBoundsToSketch([0.0, u, 0.0, v], sk)
    for i in range(int(sk.GeometryCount)):
        sk.toggleConstruction(i)


class SoS:
    def get_selection(self):
        sketch = None
        face_link = []
        sel = FreeCADGui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.Object.TypeId == 'Sketcher::SketchObject':
                sketch = selobj.Object
            elif selobj.HasSubObjects:
                if issubclass(type(selobj.SubObjects[0]), Part.Face):
                    face_link = (selobj.Object, [selobj.SubElementNames[0]])
        return sketch, face_link

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sketch, face_link = self.get_selection()
        if not sketch and not face_link:
            FreeCAD.Console.PrintMessage("Please select a face (in the 3D view) or a sketch\n")
            return
        if not sketch:
            sketch = doc.addObject('Sketcher::SketchObject', 'Mapped_Sketch')
            if hasattr(sketch, "AttachmentSupport"):
                sketch.AttachmentSupport = face_link
            else:
                sketch.Support = face_link
            n = eval(face_link[1][0].lstrip('Face'))
            fa = face_link[0].Shape.Faces[n-1]
            build_sketch(sketch, fa)
            doc.recompute()
        sos = doc.addObject("Part::FeaturePython", "Sketch On Surface")
        sketchOnSurface(sos)
        sos.Sketch = sketch
        sosVP(sos.ViewObject)
        doc.recompute()
        sketch.ViewObject.Visibility = False

    def GetResources(self):
        return {'Pixmap': TOOL_ICON,
                'MenuText': __title__,
                'ToolTip': __doc__}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('SoS', SoS())
