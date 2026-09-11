# SPDX-License-Identifier: LGPL-2.1-or-later

__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Additional tools for BSpline surfaces'


import Part
from freecad.Curves.lib.geometry import same_direction
from freecad.Curves.lib.precision import tol3d


# class BSplineFacade:
#     def __init__(self, surf, direction):
#         self.surf = surf
#         self.direction = direction
#
#     def __getattr__(self, attr):
#         pass


def get_continuities(surf: Part.BSplineSurface) -> tuple[int, int]:
    "Returns the continuities (as integer) in U and V directions"
    umults = surf.getUMultiplicities()
    vmults = surf.getVMultiplicities()
    if surf.isUPeriodic():
        umax = max(umults)
    elif len(umults) > 2:
        umax = max(umults[1:-1])
    else:
        umax = 0
    if surf.isVPeriodic():
        vmax = max(vmults)
    elif len(vmults) > 2:
        vmax = max(vmults[1:-1])
    else:
        vmax = 0
    udeg = surf.UDegree
    vdeg = surf.VDegree
    return udeg - umax, vdeg - vmax


def inner_knots_indices(surf: Part.BSplineSurface,
                        direction: int = 0) -> tuple[int, int]:
    """
    Returns the first and last indices of the inner knots of the surface.
    direction is either 0 for U or 1 for V
    """
    periodic = surf.isUPeriodic()
    nb_knots = surf.NbUKnots
    if direction == 1:
        periodic = surf.isVPeriodic()
        nb_knots = surf.NbVKnots
    if periodic:
        return 1, nb_knots + 1
    else:
        return 2, nb_knots


def get_continuity_knots(surf: Part.BSplineSurface,
                         direction: int = 0,
                         order: int = 1,
                         exact: bool = False) -> list[int]:
    """
    Returns a list of indices of the knots with continuity
    equal to order.
    direction is either 0 for U or 1 for V
    if exact is False, include the knots with continuity lower than order
    """
    knots = []
    mult = surf.getUMultiplicity
    degree = surf.UDegree
    if direction == 1:
        mult = surf.getVMultiplicity
        degree = surf.VDegree
    for j in range(*inner_knots_indices(surf, direction)):
        m = mult(j)
        print(f"Knot #{j} C{degree - m}")
        tm = degree - order
        if exact:
            match = m == tm + 1
        else:
            match = m > tm
        if match:
            knots.append(j)
    return knots


def raise_continuity(surf: Part.BSplineSurface,
                     direction: int = 0,
                     order: int = 1,
                     tol: float = 1e-7) -> bool:
    """
    Try to raise the continuity up to order.
    direction is either 0 for U or 1 for V
    Returns success status
    """
    # print(surf)
    success = True
    degree = surf.UDegree
    mult = surf.getUMultiplicity
    remove_knot = surf.removeUKnot
    if direction == 1:
        degree = surf.VDegree
        mult = surf.getVMultiplicity
        remove_knot = surf.removeVKnot
    if order > degree:
        raise ValueError("Continuity cannot be higher than degree")
    i, lki = inner_knots_indices(surf, direction)
    while i < lki:
        m = mult(i)
        print(f"Knot #{i} C{degree - m}")
        tm = degree - order
        if m > tm:
            res = remove_knot(i, tm, tol)
            if res:
                print(f"      Continuity increased to {order}")
            else:
                print(f"!!!!! Failed to increase Continuity to {order}")
            success = success and res
            if res and tm == 0:  # knot was removed, we don't increment index
                continue
        i += 1
    return success


def reverseU(surf: Part.BSplineSurface) -> Part.BSplineSurface:
    "Reverse the U direction of a BSpline surface."
    c = surf.vIso(surf.getVKnot(1))
    c.reverse()
    poles = surf.getPoles()[::-1]
    weights = surf.getWeights()[::-1]
    uknots = c.getKnots()
    umults = c.getMultiplicities()
    vknots = surf.getVKnots()
    vmults = surf.getVMultiplicities()
    uper = surf.isUPeriodic()
    vper = surf.isVPeriodic()
    udeg = surf.UDegree
    vdeg = surf.VDegree
    bs = Part.BSplineSurface()
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                uper, vper, udeg, vdeg, weights)
    return bs


def reverseV(surf: Part.BSplineSurface) -> Part.BSplineSurface:
    "Reverse the V direction of a BSpline surface."
    c = surf.uIso(surf.getUKnot(1))
    c.reverse()
    poles = [row[::-1] for row in surf.getPoles()]
    weights = [row[::-1] for row in surf.getWeights()]
    uknots = surf.getUKnots()
    umults = surf.getUMultiplicities()
    vknots = c.getKnots()
    vmults = c.getMultiplicities()
    uper = surf.isUPeriodic()
    vper = surf.isVPeriodic()
    udeg = surf.UDegree
    vdeg = surf.VDegree
    bs = Part.BSplineSurface()
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                uper, vper, udeg, vdeg, weights)
    return bs


def orientU_surf(s, cidx, end=False):
    if cidx > 1:
        s.exchangeUV()
        cidx -= 2
    if cidx == 0 and end:
        return reverseU(s)
    if cidx == 1 and not end:
        return reverseU(s)
    return s


def surface_boundaries(surf: Part.BSplineSurface):
    """
    Return a list of four boundary curves of a surface:
    [uIso(u0), uIso(u1), vIso(v0), vIso(v1)]
    """
    u0, u1, v0, v1 = surf.bounds()
    uiso = [surf.uIso(u) for u in [u0, u1]]
    viso = [surf.vIso(v) for v in [v0, v1]]
    return uiso + viso


def match_orientation(s1: Part.BSplineSurface,
                      s2: Part.BSplineSurface,
                      num_samples: int = 5
                      ) -> (Part.BSplineSurface, Part.BSplineSurface):
    """
    Match the U/V orientation of two BSpline surfaces
    that are touching by one of their boundaries.
    """

    idx1 = 0
    idx2 = 0
    dist = 1e50
    curves1 = surface_boundaries(s1)
    curves2 = surface_boundaries(s2)
    for i, c1 in enumerate(curves1):
        e1 = c1.toShape()
        for j, c2 in enumerate(curves2):
            try:
                pts = c2.discretize(num_samples)
            except Part.OCCError:
                # print("Degenerated edge. Ignoring.")
                continue
            dl = [Part.Vertex(p).distToShape(e1)[0] for p in pts]
            dsum = sum(dl)
            if dsum < dist:
                dist = dsum
                idx1 = i
                idx2 = j

    same_dir = same_direction(curves1[idx1], curves2[idx2])
    # print(f"contact {idx1}->{idx2}, same direction:{same_dir}")
    ns1 = orientU_surf(s1, idx1, True)
    ns2 = orientU_surf(s2, idx2, False)
    if not same_dir:
        ns2 = reverseU(ns2)
    return ns1, ns2


def average_U_length(surf: Part.BSplineSurface,
                     num_samples: int = 3
                     ) -> float:
    """
    Returns the average length of surface along U dirction
    """
    u0, u1, v0, v1 = surf.bounds()
    params = []
    if num_samples == 1:
        params = [0.5 * (v0 + v1)]
    else:
        for i in range(num_samples + 1):
            params.append(v0 + i * (v1 - v0) / num_samples)
    total_length = 0
    for par in params:
        c = surf.vIso(par)
        total_length += c.length()
    return total_length / num_samples


def average_V_length(surf: Part.BSplineSurface,
                     num_samples: int = 3
                     ) -> float:
    """
    Returns the average length of surface along V dirction
    """
    u0, u1, v0, v1 = surf.bounds()
    params = []
    if num_samples == 1:
        params = [0.5 * (u0 + u1)]
    else:
        for i in range(num_samples + 1):
            params.append(u0 + i * (u1 - u0) / num_samples)
    total_length = 0
    for par in params:
        c = surf.uIso(par)
        total_length += c.length()
    return total_length / num_samples


def join_surfaces(s1, s2, tol=tol3d):
    """
    Join two BSpline surfaces into a single one.
    """
    ul1 = average_U_length(s1, 3)
    ul2 = average_U_length(s2, 3)
    s1.scaleKnotsToBounds(0, ul1, 0, 1)
    s2.scaleKnotsToBounds(ul1, ul1 + ul2, 0, 1)  # TODO Check parametrization
    c1 = s1.uIso(ul1)
    c2 = s2.uIso(ul1)
    ruled = Part.makeRuledSurface(c1.toShape(), c2.toShape())
    c = ruled.Surface.vIso(0.0)
    # Part.show(c.toShape())
    vdeg = c.Degree
    udeg = max(s1.UDegree, s2.UDegree)
    s1.increaseDegree(udeg, vdeg)
    s2.increaseDegree(udeg, vdeg)
    kl = c.getKnots()
    ml = c.getMultiplicities()
    s1.insertVKnots(kl, ml, tol3d, False)
    s2.insertVKnots(s1.getVKnots(), s1.getVMultiplicities(), tol3d, False)
    s1.insertVKnots(s2.getVKnots(), s2.getVMultiplicities(), tol3d, False)
    # for i in range(len(kl)):
    # Part.show(s1.toShape())
    # Part.show(s2.toShape())
    # print(f"{len(s2.getPoles())}x{len(s2.getPoles()[0])}")
    # build poles array
    poles = s1.getPoles()[:-1]
    midpoles = [0.5 * (v[0] + v[1]) for v in zip(s1.getPoles()[-1], s2.getPoles()[0])]
    # print(len(midpoles))
    poles.append(midpoles)
    poles.extend(s2.getPoles()[1:])
    # print(f"{len(poles)}x{len(poles[0])}")
    # build weights array
    weights = s1.getWeights()[:-1]
    midweights = [0.5 * (v[0] + v[1]) for v in zip(s1.getWeights()[-1], s2.getWeights()[0])]
    weights.append(midweights)
    weights.extend(s2.getWeights()[1:])
    # weights = surf.getWeights()[::-1]
    uknots = s1.getUKnots() + s2.getUKnots()[1:]
    umults = s1.getUMultiplicities()
    umults[-1] -= 1
    umults.extend(s2.getUMultiplicities()[1:])
    vknots = s1.getVKnots()  # + s2.getVKnots()[1:]
    vmults = s1.getVMultiplicities()
    # vmults[-1] -= 1
    # vmults.extend(s2.getVMultiplicities()[1:])
    uper = s1.isUPeriodic() and s2.isUPeriodic()
    vper = s1.isVPeriodic() and s2.isVPeriodic()
    # print(f"{len(poles)}x{len(poles[0])}", umults, vmults, uknots, vknots,
    #       uper, vper, udeg, vdeg, f"{len(weights)}x{len(weights[0])}")

    bs = Part.BSplineSurface()
    bs.buildFromPolesMultsKnots(poles, umults, vmults, uknots, vknots,
                                uper, vper, udeg, vdeg, weights)
    return bs
