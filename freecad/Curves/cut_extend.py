import Part

class CutExtendShape:
    def __init__(self, shape, cutter, distance):
        self.input_shape = shape
        u0, u1, v0, v1 = cutter.ParameterRange
        u = 0.5 * (u0 + u1)
        v = 0.5 * (v0 + v1)
        self.normal = cutter.normalAt(u, v)
        self.cutter = cutter.Face1.Surface.toShape()
        self.distance = distance

    def get_half_space(self):
        margin = 1e5
        common = self.cutter.common([self.input_shape])
        u0l = []
        u1l = []
        v0l = []
        v1l = []
        for f in common.Faces:
            u0, u1, v0, v1 = f.ParameterRange
            u0l.append(u0)
            u1l.append(u1)
            v0l.append(v0)
            v1l.append(v1)
        u0 = min(u0l)
        u1 = max(u1l)
        v0 = min(v0l)
        v1 = max(v1l)
        rts = Part.RectangularTrimmedSurface(self.cutter.Surface, u0 - margin, u1 + margin, v0 - margin, v1 + margin)
        self.cut_face = rts.toShape()
        dist = self.input_shape.BoundBox.DiagonalLength
        cut_solid = self.cut_face.extrude(self.normal * dist)
        return cut_solid

    def extend(self):
        solid = self.get_half_space()
        cop1 = self.input_shape.copy()
        cut = cop1.cut([solid])
        cop2 = self.input_shape.copy()
        common = cop2.common([solid])
        common.translate(self.normal * self.distance)
        interface = self.input_shape.common(self.cut_face)
        ext = interface.extrude(self.normal * self.distance)
        fuse = cut.fuse([ext, common])
        return fuse
