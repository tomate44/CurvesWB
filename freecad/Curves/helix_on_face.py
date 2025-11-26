# SPDX-License-Identifier: LGPL-2.1-or-later

def helix_on_face(face, turns=1.0, wire_output=True):
    """
    Create an helix shape on a periodic face.
    helix_shape = helix_on_face(face, turns=1.0, wire_output=True)
    If wire_output is False, helix_shape will be a single edge.
    However, for a high number of turns, OCCT may fail and return some weird result.
    If wire_output is True, helix_shape will be a wire made of single turn edges.
    """
    u0,u1,v0,v1 = face.ParameterRange
    if face.Surface.isUPeriodic():
        ls = Part.Geom2d.Line2dSegment(FreeCAD.Base.Vector2d(u0, v0), FreeCAD.Base.Vector2d(u0 + ((u1-u0) * turns), v1))
    elif face.Surface.isVPeriodic():
        ls = Part.Geom2d.Line2dSegment(FreeCAD.Base.Vector2d(u0, v0), FreeCAD.Base.Vector2d(u1, v0 + ((v1-v0) * turns)))
    else:
        print("Error: Face is not periodic")
        return None
    if not wire_output:
        return ls.toShape(face.Surface)
    pts = ls.discretize(Distance=ls.length()/turns)
    edges = []
    for i in range(len(pts)-1):
        edges.append(Part.Geom2d.Line2dSegment(pts[i], pts[i+1]).toShape(face.Surface))
    return Part.Wire(edges)

face = FreeCADGui.Selection.getSelectionEx()[0].SubObjects[0]
helix_shape = helix_on_face(face, 100.0)
Part.show(helix_shape)

