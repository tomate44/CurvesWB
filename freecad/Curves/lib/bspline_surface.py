# SPDX-License-Identifier: LGPL-2.1-or-later

__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Additional tools for BSpline surfaces'


import Part
from freecad.Curves.lib.geometry import same_direction
from freecad.Curves.lib.precision import tol3d


def get_continuities(surf: Part.BSplineSurface) -> tuple[int, int]:
    "Returns the continuities (as integer) in U and V directions"
    umults = surf.getUMultiplicities()
    vmults = surf.getVMultiplicities()
    if surf.isUPeriodic():
        umax = max(umults)
    else:
        umax = max(umults[1:-1])
    if surf.isVPeriodic():
        vmax = max(vmults)
    else:
        vmax = max(vmults[1:-1])
    udeg = surf.UDegree
    vdeg = surf.VDegree
    return udeg - umax, vdeg - vmax


def raise_continuityU(surf: Part.BSplineSurface,
                      order: int = 1,
                      tol: float = 1e-7) -> bool:
    """
    Try to raise the continuity in U direction up to order
    Returns success status
    """
    udeg = surf.UDegree
    success = True
    if order > udeg:
        raise ValueError("Continuity cannot be higher than degree")
    if surf.isUPeriodic():
        i = 1
        lastidx = surf.NbUKnots + 1
    else:
        i = 2
        lastidx = surf.NbUKnots
    while i < lastidx:
        m = surf.getUMultiplicity(i)
        print(f"Knot #{i} C{udeg - m}")
        tm = udeg - order
        if m > tm:
            res = surf.removeUKnot(i, tm, tol)
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


def surface_boundaries(surf: Part.Surface):
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
                # print("Degenerated edge. Ignoring.")
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


def join_surfaces(s1, s2, tol=tol3d):
    """
    Join two BSpline surfaces into a single one.
    """
    s1.scaleKnotsToBounds()
    s2.scaleKnotsToBounds(1, 2, 0, 1)  # TODO Check parametrization
    c1 = s1.uIso(1.0)
    c2 = s2.uIso(1.0)
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
