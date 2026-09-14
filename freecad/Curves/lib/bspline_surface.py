# SPDX-License-Identifier: LGPL-2.1-or-later

__author__ = 'Christophe Grellier (Chris_G)'
__license__ = 'LGPL 2.1'
__doc__ = 'Additional tools for BSpline surfaces'


import Part
from freecad.Curves.lib.geometry import same_direction
from freecad.Curves.lib.precision import tol3d, tol2d


class BSplineFacade:
    '''
    Facade pattern that permits to use BSplineCurve methods and attributes
    on the choosen direction of a BSplineSurface.

    Attributes:
    surf: Part.BSplineSurface
    direction: int (0 or 1) for U or V
    '''
    attrlist = {"Degree": ("UDegree", "VDegree"),
                "NbKnots": ("NbUKnots", "NbVKnots"),
                "NbPoles": ("NbUPoles", "NbVPoles"),
                "FirstUKnotIndex": ("FirstUKnotIndex", "FirstVKnotIndex"),
                "LastUKnotIndex": ("LastUKnotIndex", "LastVKnotIndex"),
                "getKnot": ("getUKnot", "getVKnot"),
                "getKnots": ("getUKnots", "getVKnots"),
                "getMultiplicity": ("getUMultiplicity", "getVMultiplicity"),
                "getMultiplicities": ("getUMultiplicities", "getVMultiplicities"),
                "increaseMultiplicity": ("increaseUMultiplicity", "increaseVMultiplicity"),
                "incrementMultiplicity": ("incrementUMultiplicity", "incrementVMultiplicity"),
                "insertKnot": ("insertUKnot", "insertVKnot"),
                "insertKnots": ("insertUKnots", "insertVKnots"),
                "isClosed": ("isUClosed", "isVClosed"),
                "isPeriodic": ("isUPeriodic", "isVPeriodic"),
                "isRational": ("isURational", "isVRational"),
                "removeKnot": ("removeUKnot", "removeVKnot"),
                "setKnot": ("setUKnot", "setVKnot"),
                "setKnots": ("setUKnots", "setVKnots"),
                "setNotPeriodic": ("setUNotPeriodic", "setVNotPeriodic"),
                "setOrigin": ("setUOrigin", "setVOrigin"),
                "setPeriodic": ("setUPeriodic", "setVPeriodic"),
                "isoCurve": ("uIso", "vIso")}

    def __init__(self,
                 surf: Part.BSplineSurface,
                 direction: int = 0):
        self.surf = surf
        self.direction = direction

    def __getattr__(self, attr):
        if hasattr(self.surf, attr):
            return getattr(self.surf, attr)
        newattr = BSplineFacade.attrlist[attr][self.direction]
        return getattr(self.surf, newattr)


def get_continuities(surf: Part.BSplineSurface) -> tuple[int, int]:
    "Returns the continuities (as integer) in U and V directions"
    def get_cont(surf: BSplineFacade) -> int:
        mults = surf.getMultiplicities()
        if surf.isPeriodic():
            umax = max(mults)
        elif len(mults) > 2:
            umax = max(mults[1:-1])
        else:
            umax = 0
        return surf.Degree - umax
    bsf = BSplineFacade(surf, 0)
    ucont = get_cont(bsf)
    bsf.direction = 1
    vcont = get_cont(bsf)
    return ucont, vcont


def inner_knots_indices(surf: Part.BSplineSurface,
                        direction: int = 0) -> tuple[int, int]:
    """
    Returns the first and last indices of the inner knots of the surface.
    direction is either 0 for U or 1 for V
    """
    bsf = BSplineFacade(surf, direction)
    if bsf.isPeriodic():
        return 1, bsf.NbKnots + 1
    else:
        return 2, bsf.NbKnots


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
    bsf = BSplineFacade(surf, direction)
    mult = bsf.getMultiplicity
    degree = bsf.Degree
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
                     tol: float = tol3d) -> bool:
    """
    Try to raise the continuity up to order.
    direction is either 0 for U or 1 for V
    Returns success status
    """
    # print(surf)
    success = True
    bsf = BSplineFacade(surf, direction)
    if order > bsf.Degree:
        raise ValueError("Continuity cannot be higher than degree")
    i, lki = inner_knots_indices(surf, direction)
    while i < lki:
        m = bsf.getMultiplicity(i)
        # print(f"Knot #{i} C{bsf.Degree - m}")
        tm = bsf.Degree - order
        if m > tm:
            res = bsf.removeKnot(i, tm, tol)
            # if res:
            #     print(f"      Continuity increased to {order}")
            # else:
            #     print(f"!!!!! Failed to increase Continuity to {order}")
            success = success and res
            if res and tm == 0:  # knot was removed, we don't increment index
                continue
        i += 1
    dirstr = "U"
    if direction == 1:
        dirstr = "V"
    resstr = "OK"
    if not success:
        resstr = "Failed"
    print(f"Raising surface {dirstr} continuity to C{order} : {resstr}")
    return success


def smooth_surface(surf: Part.BSplineSurface,
                   distance: float = 1.0,
                   order: int = 1,
                   tol: float = tol3d
                   ) -> None:
    """
    Smooth surface up to continuity 'order' by rounding areas
    given by distance around low continuity knots
    """
    for direction in [0, 1]:
        bsf = BSplineFacade(surf, direction)
        bad_knots = get_continuity_knots(surf, direction, order - 1, False)
        print(f"Bad Knots : {bad_knots}")
        insknots = []
        for knot in bad_knots:
            if direction == 0:
                curves = isocurves_U(surf, 5)
            else:
                curves = isocurves_V(surf, 5)
            kl1, kl2 = [], []
            for c in curves:
                kl1.append(c.parameterAtDistance(-distance, knot))
                kl2.append(c.parameterAtDistance(distance, knot))
            k1 = max(kl1)
            k2 = min(kl2)
            print(f"Neighbor knots : {k1} < {knot} < {k2}")
            knots1 = [k1 + i * (knot - k1) / bsf.Degree for i in range(bsf.Degree)]
            knots2 = [knot + i * (k2 - knot) / bsf.Degree for i in range(1, bsf.Degree + 1)]
            print(f"New knots before : {knots1}")
            print(f"New knots after :  {knots2}")
            insknots += knots1 + knots2
        for k in insknots:
            if direction == 0:
                surf.insertUKnot(k, 1, tol3d)
            else:
                surf.insertVKnot(k, 1, tol3d)
    return surf


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


def isocurves_U(surf: Part.BSplineSurface,
                num_samples: int = 3
                ) -> list[Part.BSplineCurve]:
    "Returns some U isocurves of the surface"
    u0, u1, v0, v1 = surf.bounds()
    params = []
    if num_samples == 1:
        params = [0.5 * (u0 + u1)]
    else:
        for i in range(num_samples + 1):
            params.append(u0 + i * (u1 - u0) / num_samples)
    return [surf.uIso(par) for par in params]


def isocurves_V(surf: Part.BSplineSurface,
                num_samples: int = 3
                ) -> list[Part.BSplineCurve]:
    "Returns some V isocurves of the surface"
    u0, u1, v0, v1 = surf.bounds()
    params = []
    if num_samples == 1:
        params = [0.5 * (v0 + v1)]
    else:
        for i in range(num_samples + 1):
            params.append(v0 + i * (v1 - v0) / num_samples)
    return [surf.vIso(par) for par in params]


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


def join_surfaces(surf1: Part.BSplineSurface,
                  surf2: Part.BSplineSurface,
                  tol_2d: float = tol2d,
                  tol_3d: float = tol3d,
                  ) -> Part.BSplineSurface:
    """
    Join two BSpline surfaces into a single one.
    """
    s1, s2 = match_orientation(surf1, surf2)
    d, pts, info = s1.toShape().distToShape(s2.toShape())
    if d > tol_3d:  # Surfaces are not touching
        c1 = s1.uIso(s1.bounds()[1])
        c2 = s2.uIso(s2.bounds()[0])
        ruled = Part.makeRuledSurface(c1.toShape(), c2.toShape()).Surface
        # ruled.exchangeUV()
        s1 = join_surfaces(s1, ruled, tol_2d, tol_3d)
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
    s1.insertVKnots(kl, ml, tol_2d, False)
    s2.insertVKnots(s1.getVKnots(), s1.getVMultiplicities(), tol_2d, False)
    s1.insertVKnots(s2.getVKnots(), s2.getVMultiplicities(), tol_2d, False)
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


def join_multiple_surfaces(surflist: list[Part.BSplineSurface],
                           tol: float = tol2d
                           ) -> Part.BSplineSurface:
    """
    Join multiple BSpline surfaces into a single one.
    """
    if len(surflist) == 0:
        raise ValueError("Surface list is empty")
    if len(surflist) == 1:
        return surflist[0]
    s1, s2 = surflist[:2]
    # s1, s2 = match_orientation(s1, s2)
    result = join_surfaces(s1, s2, tol)
    if len(surflist) == 2:
        return result
    for i in range(2, len(surflist)):
        s2 = surflist[i]
        # s1, s2 = match_orientation(result, s2)
        result = join_surfaces(result, s2, tol)
    return result
