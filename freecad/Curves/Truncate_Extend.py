class TruncateExtend:
    """Truncate or extend a shape by a given distance
    te = TruncateExtend(shape, cutter, distance)
    result_shape = te.Shape
    'shape' is the shape to truncate or extend
    'cutter' is the planar shape that cuts the input shape
    'distance' is the length to truncate (if negative) or extend (if positive)
    """
    def __init__(self, shape, cutter, distance):
        self.input_shape = shape
        u0, u1, v0, v1 = cutter.ParameterRange
        u = 0.5 * (u0 + u1)
        v = 0.5 * (v0 + v1)
        self.normal = cutter.normalAt(u, v)
        self.cutter = cutter.Face1.Surface.toShape()
        self.distance = distance

    def get_half_space(self):
        dist = self.input_shape.BoundBox.DiagonalLength
        cut_solid = self.cutter.extrude(self.normal * dist)
        return cut_solid

    def extend(self):
        solid = self.get_half_space()
        cut = self.input_shape.cut([solid])
        common = self.input_shape.common([solid])
        common.translate(self.normal * self.distance)
        if self.distance <= 0.0:
            return cut.fuse([common])
        interface = self.input_shape.common(self.cutter)
        ext = interface.extrude(self.normal * self.distance)
        fuse = cut.fuse([ext, common])
        return fuse

    @property
    def Shape(self):
        return self.extend()
