import FreeCAD
import Part

error = FreeCAD.Console.PrintError


def debug(str):
    return


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
        if self.surface is not None:
            f = Part.Face(self.surface, w2)
        else:
            f = Part.Face(w2)
        if not f.isValid():
            f.validate()
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


def build_faces(wl, face):
    faces = []
    for w in wl:
        w.fixWire(face, 1e-7)
    bs = BoundarySorter(wl, face.Surface, True)
    for i, wirelist in enumerate(bs.sort()):
        # print(wirelist)
        f = Part.Face(face.Surface, wirelist[0])
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
        # f.sewShape()
        # f.check(True)
        # print_tolerance(f)
        if not f.isValid():
            error("{:3}:Invalid final face".format(i))
        faces.append(f)
    return faces
