import FreeCADGui
import splipy

s = FreeCADGui.Selection.getSelectionEx()
e1 = s[0].SubObjects[0]
c1 = e1.Curve
c2 = s[1].SubObjects[0].Curve

def curvematch(c1,c2,level=0,scale=1.0):

    c1 = c1.toNurbs()
    c2 = c2.toNurbs()

    c1end = c1.LastParameter
    c2sta = c2.FirstParameter

    p1 = c1.getPoles()
    p2 = c2.getPoles()

    seq = c2.KnotSequence
    seq = [k*scale for k in seq]

    basis1 = splipy.BSplineBasis(order=int(c1.Degree)+1, knots=c1.KnotSequence)
    basis2 = splipy.BSplineBasis(order=int(c2.Degree)+1, knots=seq)

    l = 0
    while l <= level:
        FreeCAD.Console.PrintMessage("\nDerivative %d\n"%l)
        ev1 = basis1.evaluate(c1end,d=l).A1.tolist()
        ev2 = basis2.evaluate(c2sta,d=l).A1.tolist()
        FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev1))
        FreeCAD.Console.PrintMessage("Basis %d - %r\n"%(l,ev2))
        pole1 = FreeCAD.Vector()
        for i in range(len(ev1)):
            pole1 += 1.0*ev1[i]*p1[i]
        val = ev2[l]
        if val == 0:
            FreeCAD.Console.PrintError("Zero !\n")
            break
        else:
            pole2 = FreeCAD.Vector()
            for i in range(l):
                pole2 += 1.0*ev2[i]*p2[i]
            np = (1.0*pole1-pole2)/val
            FreeCAD.Console.PrintMessage("Moving P%d from (%0.2f,%0.2f,%0.2f) to (%0.2f,%0.2f,%0.2f)\n"%(l,p2[l].x,p2[l].y,p2[l].z,np.x,np.y,np.z))
            p2[l] = np
        l += 1
    nc = c2.copy()
    for i in range(len(p2)):
        nc.setPole(i+1,p2[i])
    return(nc)

curve = curvematch(c1,c2,2,1.0)

edge = curve.toShape()
d11 = e1.derivative1At(e1.LastParameter)
d12 = e1.derivative2At(e1.LastParameter)
d13 = e1.derivative3At(e1.LastParameter)

d21 = edge.derivative1At(edge.FirstParameter)
d22 = edge.derivative2At(edge.FirstParameter)
d23 = edge.derivative3At(edge.FirstParameter)

FreeCAD.Console.PrintMessage("\nDerivative 1\n%r / %r"%(d11,d21))
FreeCAD.Console.PrintMessage("\nDerivative 2\n%r / %r"%(d12,d22))
FreeCAD.Console.PrintMessage("\nDerivative 3\n%r / %r"%(d13,d23))

Part.show(edge)


