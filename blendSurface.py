import Part
import curveOnSurface

def getEdge(obj):
    res = None
    if hasattr(obj, "InputEdge"):
        o = obj.InputEdge[0]
        ss = obj.InputEdge[1][0]
        n = eval(ss.lstrip('Edge'))
        res = o.Shape.Edges[n-1]
    return(res)

def getFace(obj):
    res = None
    if hasattr(obj, "Face"):
        o = obj.Face[0]
        ss = obj.Face[1][0]
        n = eval(ss.lstrip('Face'))
        res = o.Shape.Faces[n-1]
    return(res)

def paramRange(cos):
    return(cos.lastParameter - cos.firstParameter)

s = FreeCADGui.Selection.getSelection()

o1 = s[0]
o2 = s[1]

e1 = getEdge(o1)
e2 = getEdge(o2)
f1 = getFace(o1)
f2 = getFace(o2)

cos1 = curveOnSurface.curveOnSurface(e1,f1)
cos2 = curveOnSurface.curveOnSurface(e2,f2)

cos1.reverseTangent =  o1.ReverseTangent
cos1.reverseNormal =   o1.ReverseNormal
cos1.reverseBinormal = o1.ReverseBinormal

cos2.reverseTangent =  o2.ReverseTangent
cos2.reverseNormal =   o2.ReverseNormal
cos2.reverseBinormal = o2.ReverseBinormal

samples = 20
curves = []


for i in range(samples):
    t1 = cos1.firstParameter + (1.0 * i * paramRange(cos1) / (samples - 1))
    t2 = cos2.firstParameter + (1.0 * i * paramRange(cos2) / (samples - 1))
    #t2 = cos2.lastParameter - (1.0 * i * paramRange(cos2) / (samples - 1))
    pt1 = cos1.valueAt(t1)
    pt2 = cos2.valueAt(t2)
    chord = pt2.sub(pt1).Length
#    ip1 = cos1.tangentTo(t1,pt2)[0]
#    ip2 = cos2.tangentTo(t2,pt1)[0]
    ip1 = cos1.binormalAt(t1)
    ip2 = cos2.binormalAt(t2)
    ip1.normalize().multiply(chord / 3.0)
    ip2.normalize().multiply(chord / 3.0)
    poles = [pt1, pt1.add(ip1), pt2.add(ip2), pt2]
    bz = Part.BezierCurve()
    bz.setPoles(poles)
    curves.append(bz)


for c in curves:
    e = c.toShape()
    Part.show(e)


    
