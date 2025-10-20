# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui as Gui
import Part
vec = FreeCAD.Vector
vec2 = FreeCAD.Base.Vector2d


def wire(e1, e2):
    """
    w = wire(edge_1,edge_2)
    returns a valid wire, or None
    """
    w = Part.Wire([e1, e2])
    if w.isValid():
        return w
    else:
        print("Failed to build wire")
    return None


def longest_edge(e1, e2):
    """
    long_edge = longest_edge(e1,e2)
    """
    if e1.Length > e2.Length:
        return e1
    else:
        return e2


def longest_segment(e, p):
    """
    long_edge = longest_segment(Edge, Parameter)
    returns the longest part of edge e split at parameter p
    """
    w = e.split(p)
    return longest_edge(w.Edges[0], w.Edges[1])


def join_2_edges(e1, e2, tol=1e-7):
    d, pts, info = e1.distToShape(e2)
    if d < tol:  # edges are touching
        for i in info:
            if (i[0] == "Vertex") and (i[3] == "Vertex"):  # Contact type : end to end
                return (e1, e2)
            elif (i[0] == "Edge") and (i[3] == "Vertex"):  # Contact type : edge to end
                return (longest_segment(e1, i[2]), e2)
            elif (i[0] == "Vertex") and (i[3] == "Edge"):  # Contact type : end to edge
                return (e1, longest_segment(e2, i[5]))
            elif (i[0] == "Edge") and (i[3] == "Edge"):  # Contact type : edge to edge
                return (longest_segment(e1, i[2]), longest_segment(e2, i[5]))
    else:  # No contact : must add a join curve
        for pt, i in zip(pts, info):
            line = Part.makeLine(pt[0], pt[1])
            if (i[0] == "Vertex") and (i[3] == "Vertex"):  # Contact type : end to end
                return (e1, line, e2)
            elif (i[0] == "Edge") and (i[3] == "Vertex"):  # Contact type : edge to end
                return (longest_segment(e1, i[2]), line, e2)
            elif (i[0] == "Vertex") and (i[3] == "Edge"):  # Contact type : end to edge
                return (e1, line, longest_segment(e2, i[5]))
            elif (i[0] == "Edge") and (i[3] == "Edge"):  # Contact type : edge to edge
                return (longest_segment(e1, i[2]), line, longest_segment(e2, i[5]))


def join_multi_edges(edge_list, closed=False, tol=1e-7):
    edgelist = []
    for e in edge_list:
        edgelist.append(e.Curve.toShape(e.FirstParameter, e.LastParameter))
    good_edges = list()
    last = edgelist[0]
    remaining = edgelist[1:]
    res = []
    while len(remaining) > 0:
        rejected = list()
        closest_dist = 1e50
        closest_edge = None
    #    closest_pts = None
    #    closest_info = None
        for e in remaining:
            d, p, i = e.distToShape(last)
            if closest_dist > d:
                closest_dist = d
                if closest_edge:
                    rejected.append(closest_edge)
                closest_edge = e
    #            closest_pts  = p
    #            closest_info = i
            else:
                rejected.append(e)
        res = join_2_edges(last, closest_edge, tol)
        # print(last.distToShape(closest_edge))
        last = res[-1]
        good_edges.extend(res[:-1])
        remaining = rejected
    if res:
        good_edges.append(res[-1])
    se = Part.sortEdges(good_edges)
    wires = list()
    for group in se:
        print("Wire has {} edges".format(len(group)))
        wires.append(Part.Wire(group))
    if closed:
        for w in wires:
            if not w.isClosed():
                ov = w.OrderedVertexes
                d, p, i = ov[0].distToShape(ov[-1])
                w.add(Part.makeLine(p[0][0], p[0][1]))
    return Part.Compound(wires)


def run(closed=False):
    s = Gui.Selection.getSelection()
    ori_edges = s[0].Shape.Edges
    tol = s[0].Shape.getTolerance(-1, Part.Vertex)
    return join_multi_edges(ori_edges, closed, tol)


def show(closed=False):
    Part.show(run(closed))

