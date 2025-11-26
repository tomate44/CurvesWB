# SPDX-License-Identifier: LGPL-2.1-or-later

from math import pi
import Part
from . import TOL3D

def fit_edge_to_point(e1, pt, tol=TOL3D):
    """Transform an edge by rotation / scaling so that its nearest end match point.
    The opposite end is not moved.
    """
    p1 = e1.valueAt(e1.FirstParameter)
    p2 = e1.valueAt(e1.LastParameter)
    d1 = p1.distanceToPoint(pt)
    d2 = p2.distanceToPoint(pt)
    if d1 >= d2:
        origin = p1
        end = p2
    else:
        origin = p2
        end = p1
    v1 = pt - origin
    v2 = end - origin
    angle = v1.getAngle(v2)
    axis = v2.cross(v1)
    if axis.Length > tol:
        e1.rotate(origin, axis, angle * 180.0 / pi)
    scale = origin.distanceToPoint(pt) / origin.distanceToPoint(end)
    e1.scale(scale, origin)


# get edges from selection
edges = []
sel = FreeCADGui.Selection.getSelectionEx()
for s in sel:
    if s.HasSubObjects:
        edges.extend(s.SubObjects)
    else:
        edges.extend(s.Object.Shape.Edges)


# sort edges. Requires FC 0.22
sort_tol = TOL3D
sortedges = Part.sortEdges(edges, sort_tol)
while len(sortedges) > 1:
    sort_tol *= 2
    sortedges = Part.sortEdges(edges, sort_tol)

print(f"Sorting tolerance : {sort_tol}")


# Fix contact point between each edge and the following one
el = [e.copy() for e in sortedges[0]]
for i in range(len(el) - 1):
    e1 = el[i]
    e2 = el[i + 1]
    d, pts, info = e1.distToShape(e2)
    p1, p2 = pts[0]
    cpt = 0.5 * (p1 + p2)
    fit_edge_to_point(el[i], cpt)
    fit_edge_to_point(el[i + 1], cpt)

w = Part.Wire(el)
Part.show(w)

