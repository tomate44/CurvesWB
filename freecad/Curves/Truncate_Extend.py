import Part
from math import radians

class Extender:
    def __init__(self, shape, cutter, reverse=False):
        self.input_shape = shape
        u0, u1, v0, v1 = cutter.ParameterRange
        u = 0.5 * (u0 + u1)
        v = 0.5 * (v0 + v1)
        self.normal = cutter.normalAt(u, v)
        if reverse:
            self.normal = -self.normal
        self.cutter = cutter.Face1.Surface.toShape()

    def get_half_space(self):
        dist = self.input_shape.BoundBox.DiagonalLength
        cut_solid = self.cutter.extrude(self.normal * dist)
        return cut_solid


class TruncateExtend(Extender):
    """Truncate or extend a shape by a given distance
    te = TruncateExtend(shape, cutter, distance, reverse=False)
    result_shape = te.Shape
    'shape' is the shape to truncate or extend
    'cutter' is the planar shape that cuts the input shape
    'distance' is the length to truncate (if negative) or extend (if positive)
    'reverse' reverses the normal of the cutter plane
    """

    def __init__(self, shape, cutter, distance, reverse=False):
        super().__init__(shape, cutter, reverse)
        self.distance = distance

    def truncate(self):
        half_space = self.get_half_space()
        cut = self.input_shape.cut([half_space])
        half_space.translate(-self.normal * self.distance)
        common = self.input_shape.common([half_space])
        common.translate(self.normal * self.distance)
        return cut.fuse([common])

    def extend(self):
        half_space = self.get_half_space()
        cut = self.input_shape.cut([half_space])
        common = self.input_shape.common([half_space])
        common.translate(self.normal * self.distance)
        interface = self.input_shape.common(self.cutter)
        ext = interface.extrude(self.normal * self.distance)
        fuse = cut.fuse([ext, common])
        return fuse

    @property
    def Shape(self):
        if self.distance <= 0.0:
            return self.truncate()
        else:
            return self.extend()


class BendExtend(Extender):
    """Bend a shape by a given angle
    be = BendExtend(shape, cutter, axis, angle, reverse=False)
    result_shape = be.Shape
    'shape' is the shape to bend
    'cutter' is the planar shape that cuts the input shape
    'axis' is the axis of rotation of bent insert
    'angle' is the angle of rotation of bent insert
    'reverse' reverses the normal of the cutter plane
    """

    def __init__(self, shape, cutter, axis, angle, reverse=False):
        super().__init__(shape, cutter, reverse)
        self.angle = angle
        self.axis = axis
        self.cutter = cutter

    def extend(self):
        if self.angle == 0.0:
            return self.input_shape
        base = self.axis.valueAt(self.axis.FirstParameter)
        rotaxis = self.axis.tangentAt(self.axis.FirstParameter)
        half_space = self.get_half_space()
        cut = self.input_shape.cut([half_space])
        common = self.input_shape.common([half_space])
        common.rotate(base, rotaxis, self.angle)
        interface = self.input_shape.common(self.cutter)
        # axis = Part.makeLine(base, base + rotaxis)
        # d, pts, info = interface.distToShape(axis.Curve.toShape())
        # circle = Part.Circle(base, rotaxis, d)
        # fp = circle.parameter(pts[0][0])
        # lp = fp + radians(self.angle)
        # spine = circle.toShape(fp, lp)
        ext = interface.revolve(base, rotaxis, self.angle)
        # return Part.Compound([interface, ext])
        fuse = cut.fuse([ext, common])
        return fuse

    @property
    def Shape(self):
        return self.extend()
