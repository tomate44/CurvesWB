elt = App.getDocument("tide_bottle2_1_").getObject("Approximation_Curve").Shape.Face1

face = elt

pts = []
n = 32
extend = 0.01

u0,u1,v0,v1 = face.ParameterRange
ur = u1-u0
vr = v1-v0

eu0 = u0 - ur*extend
eu1 = u1 + ur*extend
ev0 = v0 - vr*extend
ev1 = v1 + vr*extend
eur = eu1-eu0
evr = ev1-ev0


for i in range(n):
    u = eu0 + 1.0 * i * eur / (n-1)
    row = []
    for j in range(n):
        v = ev0 + 1.0 * j * evr / (n-1)
        row.append(face.valueAt(u,v))
    pts.append(row)

bs = Part.BSplineSurface()
bs.approximate(Points = pts, DegMin = 3, DegMax = 5, Tolerance = 2.1, Continuity = 2, ParamType = 'ChordLength')

Part.show(bs.toShape())

