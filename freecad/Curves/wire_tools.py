from math import pi
import FreeCADGui
import Part


def angle_at_vertex(wire, vidx):
    """Return the angle of the 2 tangents of wire around vertex vidx in wire.OrderedVertexes"""
    vertex = wire.OrderedVertexes[vidx]
    parent_edges = wire.ancestorsOfType(vertex, Part.Edge)
    if len(parent_edges) == 2:
        par1 = parent_edges[0].Curve.parameter(vertex.Point)
        par2 = parent_edges[1].Curve.parameter(vertex.Point)
        t1 = parent_edges[0].tangentAt(par1)
        t2 = parent_edges[1].tangentAt(par2)
        return t1.getAngle(t2) * 180 / pi
    else:
        return 360


def approx_wire(wire, tol3d=1e-7, ang_tol=1, samples=100, forceC1=True):
    bs = wire.approximate(.01 * tol3d, tol3d, 10000, 5)
    bs.makeC1Continuous(tol3d, ang_tol)
    if bs.Continuity == "C0" and forceC1:
        print("Forcing C1 continuity")
        bs = Part.BSplineCurve()
        bs.approximate(Points=wire.discretize(samples * len(wire.Edges)),
                       DegMax=5,
                       Continuity="C1",
                       Tolerance=tol3d)
    return bs


def simplify_wire(wire, ang_tol=1, tol3d=1e-3, samples=100, forceC1=True):
    edge_groups = []
    continuous_edges = [wire.OrderedEdges[0]]
    end = len(wire.OrderedVertexes)
    if not wire.isClosed():
        end -= 1
    for i in range(1, end):
        a = angle_at_vertex(wire, i)
        if a < ang_tol:
            continuous_edges.append(wire.OrderedEdges[i])
            # print("#{} Smooth vertex : {}".format(i, a))
        else:
            edge_groups.append(continuous_edges)
            continuous_edges = [wire.OrderedEdges[i]]
            # print("#{} Sharp vertex : {}".format(i, a))
    edge_groups.append(continuous_edges)
    if (angle_at_vertex(wire, 0) < ang_tol) and (len(edge_groups) > 1):
        edge_groups[-1].extend(edge_groups[0])
        edge_groups = edge_groups[1:]
    final_edges = []
    print([len(g) for g in edge_groups])
    for group in edge_groups:
        if len(group) > 1:
            temp_wire = Part.Wire(group)
            bs = approx_wire(temp_wire, tol3d, ang_tol, samples, forceC1)
            final_edges.append(bs.toShape())
        else:
            final_edges.append(group[0])
    # print(final_edges)
    return Part.Wire(final_edges)


def _test_simplify_wire(ang_tol=1, tol3d=1e-3, samples=100, forceC1=True):
    o1 = FreeCADGui.Selection.getSelection()[0]
    wires = o1.Shape.Wires

    fixed_wires = []
    for w in wires:
        print("\nProcessing wire ...")
        fixed_wires.append(simplify_wire(w, ang_tol, tol3d, samples))

    Part.show(Part.Compound(fixed_wires))
