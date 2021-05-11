import FreeCADGui
import Part


def get_subs(s):
    el = []
    vl = []
    f = None
    for ss in s.SubObjects:
        if isinstance(ss, Part.Face):
            f = ss
        elif isinstance(ss, Part.Edge):
            el.append(ss)
        elif isinstance(ss, Part.Vertex):
            vl.append(ss)
    return f, el, vl


def vert_idx(v, w):
    for i, o in enumerate(w.OrderedVertexes):
        if o.isPartner(v):
            return i


def vert_indices(vl, w):
    il = []
    for v in vl:
        vi = vert_idx(v, w)
        if vi is not None:
            il.append(vi)
    return il


def vert_orientation(il, w):
    a, b = il[:2]
    diff = b - a
    if diff == 1 - len(w.OrderedVertexes):
        diff = 1
    if diff > 0:
        print("Forward")
        return 1
    print("Reverse")
    return -1


class MatchWires:
    """Find the best vertex connections between two wires"""
    def __init__(self, w1, w2):
        self.w1 = w1
        self.w2 = w2
        self.sh1 = None
        self.sh2 = None
        self.nb_edges = min(len(w1.Edges), len(w2.Edges))
        self.offset = 0
        self.reverse = False

    @property
    def edge_pairs(self):
        pl = []
        for idx1 in range(self.nb_edges):
            idx2 = self.calc_offset(idx1)
            pl.append([self.w1.OrderedEdges[idx1], self.w2.OrderedEdges[idx2]])
        return pl

    @property
    def offset_code(self):
        if self.reverse:
            if self.offset == 0:
                return -self.nb_edges
            return -self.offset
        return self.offset

    @offset_code.setter
    def offset_code(self, v):
        self.reverse = False
        self.offset = abs(v)
        if v < 0:
            self.reverse = True
            if abs(v) == self.nb_edges:
                self.offset = 0

    def vert_offset(self, idx1, idx2):
        diff = idx2[0] - idx1[0]
        if diff < 0:
            diff = diff + self.nb_edges
        return diff

    def calc_offset(self, i):
        if self.offset < 0:
            return (abs(self.offset) - i - 1) % self.nb_edges
        return (i + self.offset) % self.nb_edges

    def match_vertexes(self, vl1, vl2):
        idx1 = vert_indices(vl1, self.w1)
        vo1 = vert_orientation(idx1, self.w1)
        idx2 = vert_indices(vl2, self.w2)
        vo2 = vert_orientation(idx2, self.w2)
        self.offset = self.vert_offset(idx1, idx2)
        self.reverse = (vo1 * vo2) < 0
        print(f"Offset : {self.offset}")
        print(f"Reverse : {self.reverse}")
        print(f"Offset code : {self.offset_code}")


s1, s2 = FreeCADGui.Selection.getSelectionEx()
f1, el1, vl1 = get_subs(s1)
f2, el2, vl2 = get_subs(s2)

for w1, w2 in zip(f1.Wires, f2.Wires):
    mw = MatchWires(w1, w2)
    mw.match_vertexes(vl1, vl2)

#for i in range(nb):
    #id = calc_offset(i, off, nb)
    #print(f"{i} - {id}")
    #rs = Part.makeRuledSurface(f1.OuterWire.OrderedEdges[i], f2.OuterWire.OrderedEdges[id])
    #Part.show(rs)


