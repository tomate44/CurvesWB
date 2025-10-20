# SPDX-License-Identifier: LGPL-2.1-or-later

class TruncateExtend:
    """Truncate or extend a shape by a given distance
    te = TruncateExtend(shape, cutter, distance, reverse=False)
    result_shape = te.Shape
    'shape' is the shape to truncate or extend
    'cutter' is the planar shape that cuts the input shape
    'distance' is the length to truncate (if negative) or extend (if positive)
    'reverse' reverses the normal of the cutter plane
    """

    def __init__(self, shape, cutter, distance, reverse=False):
        self.input_shape = shape
        u0, u1, v0, v1 = cutter.ParameterRange
        u = 0.5 * (u0 + u1)
        v = 0.5 * (v0 + v1)
        self.normal = cutter.normalAt(u, v)
        if reverse:
            self.normal = -self.normal
        self.cutter = cutter.Face1.Surface.toShape()
        self.distance = distance

    def get_half_space(self):
        dist = self.input_shape.BoundBox.DiagonalLength
        cut_solid = self.cutter.extrude(self.normal * dist)
        return cut_solid

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
