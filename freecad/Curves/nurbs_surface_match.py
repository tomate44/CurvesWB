# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import Part

DEBUG = 1

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")

# ****** match degrees ******

def matchUDegree(s1,s2):
    '''match the UDegree of surfaces s1 and s2'''
    if   s1.UDegree > s2.UDegree:
        debug("U degree of surface 2 increased from %d to %d"%(s2.UDegree,s1.UDegree))
        s2.increaseDegree(s1.UDegree, s2.VDegree)
    elif s1.UDegree < s2.UDegree:
        debug("U degree of surface 1 increased from %d to %d"%(s1.UDegree,s2.UDegree))
        s1.increaseDegree(s2.UDegree, s1.VDegree)

def matchVDegree(s1,s2):
    '''match the VDegree of surfaces s1 and s2'''
    if   s1.VDegree > s2.VDegree:
        debug("V degree of surface 2 increased from %d to %d"%(s2.VDegree,s1.VDegree))
        s2.increaseDegree(s2.UDegree, s1.VDegree)
    elif s1.VDegree < s2.VDegree:
        debug("V degree of surface 1 increased from %d to %d"%(s1.VDegree,s2.VDegree))
        s1.increaseDegree(s1.UDegree, s2.VDegree)


# ****** match parameter ranges ******

def matchURange(s1,s2):
    '''make the UKnotSequence of surface s1 match the UKnotSequence of surface s2'''
    if not s1.UDegree == s2.UDegree:
        FreeCAD.Console.PrintError("U degree mismatch error\n")
        return(False)
    if s1.bounds()[0:2] == s2.bounds()[0:2]:
        debug("U parameter ranges already matching")
        return(True)
    s1fp, s1lp = s1.bounds()[0:2]
    s2fp, s2lp = s2.bounds()[0:2]
    s1Range = s1lp - s1fp
    s2Range = s2lp - s2fp
    newKnots = []
    for knot in s1.getUKnots():
        newKnots.append(s2fp + s2Range*(knot-s1fp)/s1Range)
    debug("UKnotSequence of surface 1 transformed from [%f,%f] to [%f,%f]"%(s1fp, s1lp, newKnots[0], newKnots[-1]))
    s1.setUKnots(newKnots)
    return(True)

def matchVRange(s1,s2):
    '''make the VKnotSequence of surface s1 match the VKnotSequence of surface s2'''
    if not s1.VDegree == s2.VDegree:
        FreeCAD.Console.PrintError("V degree mismatch error\n")
        return(False)
    if s1.bounds()[2::] == s2.bounds()[2::]:
        debug("V parameter ranges already matching")
        return(True)
    s1fp, s1lp = s1.bounds()[2::]
    s2fp, s2lp = s2.bounds()[2::]
    s1Range = s1lp - s1fp
    s2Range = s2lp - s2fp
    newKnots = []
    for knot in s1.getVKnots():
        newKnots.append(s2fp + s2Range*(knot-s1fp)/s1Range)
    debug("VKnotSequence of surface 1 transformed from [%f,%f] to [%f,%f]"%(s1fp, s1lp, newKnots[0], newKnots[-1]))
    s1.setVKnots(newKnots)
    return(True)

# ****** match knot sequences ******

def getIndex(k,ks):
    i = 1
    for n in ks:
        if n > k:
            return(i)
        else:
            i += 1
    return(i)


def matchUknots(s1,s2,tol=0.000001):
    '''insert knots to make surfaces s1 and s2 have the same U knots sequences'''
    if not s1.UDegree == s2.UDegree:
        FreeCAD.Console.PrintError("U degree mismatch error\n")
        return(False)
    if not s1.bounds()[0:2] == s2.bounds()[0:2]:
        FreeCAD.Console.PrintError("U parameter ranges mismatch error\n")
        return(False)
    k1 = s1.getUKnots()
    k2 = s2.getUKnots()
    ks = list(set(k1+k2))
    ks.sort()
    for k in ks:
        if not k in k1:
            i = getIndex(k,k1)
            s1.insertUKnot(k,i,tol)
            k1 = s1.getUKnots()
        if not k in k2:
            j = getIndex(k,k2)
            s2.insertUKnot(k,j,tol)
            k2 = s2.getUKnots()
    return(True)

def matchVknots(s1,s2,tol=0.000001):
    '''insert knots to make surfaces s1 and s2 have the same V knots sequences'''
    if not s1.VDegree == s2.VDegree:
        FreeCAD.Console.PrintError("V degree mismatch error\n")
        return(False)
    if not s1.bounds()[2::] == s2.bounds()[2::]:
        FreeCAD.Console.PrintError("V parameter ranges mismatch error\n")
        return(False)
    k1 = s1.getVKnots()
    k2 = s2.getVKnots()
    ks = list(set(k1+k2))
    ks.sort()
    for k in ks:
        if not k in k1:
            i = getIndex(k,k1)
            s1.insertVKnot(k,i,tol)
            k1 = s1.getVKnots()
        if not k in k2:
            j = getIndex(k,k2)
            s2.insertVKnot(k,j,tol)
            k2 = s2.getVKnots()
    return(True)

# ****** match multiplicities ******

def matchUMults(s1,s2):
    '''insert knots to make surfaces s1 and s2 have the same U knot multiplicities'''
    if not s1.UDegree == s2.UDegree:
        FreeCAD.Console.PrintError("U degree mismatch error\n")
        return(False)
    if not s1.bounds()[0:2] == s2.bounds()[0:2]:
        FreeCAD.Console.PrintError("U parameter ranges mismatch error\n")
        return(False)
    if not s1.getUKnots() == s2.getUKnots():
        FreeCAD.Console.PrintError("U KnotSequence mismatch error\n")
        return(False)
    m1 = s1.getUMultiplicities()
    m2 = s2.getUMultiplicities()
    for i in range(len(m1)):
        if   m1[i] > m2[i]:
            s2.increaseUMultiplicity(i+1,m1[i])
        elif m1[i] < m2[i]:
            s1.increaseUMultiplicity(i+1,m2[i])
    return(True)

def matchVMults(s1,s2):
    '''insert knots to make surfaces s1 and s2 have the same V knot multiplicities'''
    if not s1.VDegree == s2.VDegree:
        FreeCAD.Console.PrintError("V degree mismatch error\n")
        return(False)
    if not s1.bounds()[2::] == s2.bounds()[2::]:
        FreeCAD.Console.PrintError("V parameter ranges mismatch error\n")
        return(False)
    if not s1.getVKnots() == s2.getVKnots():
        FreeCAD.Console.PrintError("V KnotSequence mismatch error\n")
        return(False)
    m1 = s1.getVMultiplicities()
    m2 = s2.getVMultiplicities()
    for i in range(len(m1)):
        if   m1[i] > m2[i]:
            s2.increaseVMultiplicity(i+1,m1[i])
        elif m1[i] < m2[i]:
            s1.increaseVMultiplicity(i+1,m2[i])
    return(True)

def checkPoles(lsurf, tol=0.00001):
    s0 = lsurf[0]
    p0 = s0.getPoles()[0][0]
    p1 = s0.getPoles()[0][-1]
    p2 = s0.getPoles()[-1][0]
    d0 = 0
    d1 = 0
    d2 = 0
    for s in lsurf[1::]:
        d0 += p0.distanceToPoint(s.getPoles()[0][0])
        d1 += p1.distanceToPoint(s.getPoles()[0][-1])
        d2 += p2.distanceToPoint(s.getPoles()[-1][0])
    if (d0 < tol) and (d1 < tol) and (d2 < tol):
        debug("Poles are matching")
        return(True)
    else:
        debug("Poles are NOT matching !!! %f - %f - %f"%(d0,d1,d2))
        return(False)

def matchSurfaces(surf1,surf2):
    matchUDegree( surf1, surf2)
    matchVDegree( surf1, surf2)
    matchURange(  surf1, surf2)
    matchVRange(  surf1, surf2)
    matchUknots(  surf1, surf2)
    matchVknots(  surf1, surf2)
    matchUMults(  surf1, surf2)
    matchVMults(  surf1, surf2)


def addPoles(array1,array2):
    arr = []
    for d in range(len(array1)):
        pro = []
        for c in range(len(array1[0])):
            pro.append(array1[d][c].add(array2[d][c]))
        arr.append(pro)
    return(arr)

def subPoles(array1,array2):
    arr = []
    for d in range(len(array1)):
        pro = []
        for c in range(len(array1[0])):
            pro.append(array1[d][c].sub(array2[d][c]))
        arr.append(pro)
    return(arr)



def old_main():
    doc   = App.getDocument("Gordon_1")
    appro = doc.getObject("Approximation_Curve")
    appface  = appro.Shape.Face1

    ruled = doc.getObject("Ruled_Surface")
    rulface  = ruled.Shape.Face1
    r1    = ruled.Shape.Edge1
    r2    = ruled.Shape.Edge2

    surf1 = appface.Surface.copy()
    surf2 = rulface.Surface.copy()

    matchUDegree( surf1, surf2)
    matchURange(  surf1, surf2)
    matchVDegree( surf1, surf2)
    matchVRange(  surf1, surf2)
    matchUknots(  surf1, surf2)
    matchVknots(  surf1, surf2)
    matchUMults(  surf1, surf2)
    matchVMults(  surf1, surf2)

    # Now, the 2 surfaces should have identical topologies (same degrees, knots, mults)
    # Only their poles, weights are different

    #print(surf1.getPoles()[0])
    #print(surf2.getPoles()[0])

    surf1.exchangeUV()
    surf2.exchangeUV()

    l = len(surf1.getPoles())

    surf1.setPoleRow(1,surf2.getPoles()[0])
    surf1.setPoleRow(l,surf2.getPoles()[-1])

    Part.show(surf1.toShape())
    #Part.show(surf2.toShape())

def main():
    doc   = FreeCAD.getDocument("Gordon_1")
    
    loft = doc.getObject("Loft")
    profloft  = loft.Shape.Face1

    inter = doc.getObject("Shape")
    interpts  = inter.Shape.Face1
    
    loft2 = doc.getObject("Ruled_Surface")
    railloft = loft2.Shape.Face1


    surf1 = profloft.Surface.copy()
    surf2 = railloft.Surface.copy()
    surf3 = interpts.Surface.copy()

    surf1.exchangeUV()

    matchSurfaces(surf1, surf2)
    matchSurfaces(surf2, surf3)
    matchSurfaces(surf3, surf1)
    
    checkPoles([surf1,surf2,surf3])

    # Now, the 3 surfaces should have identical topologies (same degrees, knots, mults)
    # Only their poles, weights are different

    poles1 = addPoles(surf1.getPoles(), surf2.getPoles())
    poles2 = subPoles(poles1, surf3.getPoles())

    gordon = surf1.copy()
    for i in range(len(poles2)):
        gordon.setPoleRow(i+1, poles2[i])

    Part.show(surf1.toShape())
    Part.show(surf2.toShape())
    Part.show(surf3.toShape())
    Part.show(gordon.toShape())

if __name__ == '__main__':
    main()



