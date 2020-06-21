# fl = list of faces to compute
# cyl = cylinder face that surrounds the faces

# ***** Change direction below
dir = FreeCAD.Vector(0,1,0)

o = FreeCADGui.Selection.getSelection()[0]
fl = o.Shape.Faces

base = o.Shape.CenterOfMass
dl = o.Shape.BoundBox.DiagonalLength
cyl = Part.makeCylinder(dl, dl*2, base-dir*dl, dir).Face1


num_samples = 360*2

uf,ul,vf,vl=cyl.ParameterRange
#pts = [list()] * len(fl)
one = list()
for i in range(num_samples):
    u = uf + (float(i)/(num_samples-1))*(ul-uf)
    e = cyl.Surface.uIso(u).toShape()
    best = 1e50
    good_pt = None
    #good_idx = None
    for i,f in enumerate(fl):
        d,pt,info = f.distToShape(e)
        if d < best:
            best = d
            good_point = pt[0][0]
            #good_idx = i
    #pts[good_idx].append(good_point)
    one.append(good_point)

#for pl in pts:
    #bs = Part.BSplineCurve()
    #bs.approximate(pl)
    #Part.show(bs.toShape())



bs = Part.BSplineCurve()
bs.approximate(one)
Part.show(bs.toShape())

