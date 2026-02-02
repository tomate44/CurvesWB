import Part


"""
from freecad.Curves.lib.trimmed_surface import TrimmedSurface
ts = TrimmedSurface(f1)
"""


class TrimmedSurface:
    """Create a Trimmed Surface from
    a face or surface source.
    ts = TrimmedSurface(face)
    ts.extend(0.1)
    trim_face = ts.Face
    """

    def __repr__(self):
        return f"TrimmedSurface({str(self.basis_surf)}, {str(self.Bounds)})"

    def __init__(self, source):
        self._inf = 1e100
        if source.isDerivedFrom("Part::GeomSurface"):
            self.basis_surf = source
            self.basis_face = None
        elif isinstance(source, Part.Face):
            self.basis_surf = source.Surface
            self.basis_face = source
        self.reset_boundaries()

    def reset_boundaries(self):
        "Set boundaries to default values"
        if self.basis_face:
            pr = self.basis_face.ParameterRange
        else:
            pr = self.basis_surf.bounds()
        self.Umin, self.Umax = pr[:2]
        self.Vmin, self.Vmax = pr[2:]
        self._limit_boundaries()

    def _limit_boundaries(self):
        "Avoid infinite boundary values"
        if self.Umin < -self._inf:
            self.Umin = min(0.0, self.Umax - 1.0)
        if self.Vmin < -self._inf:
            self.Vmin = min(0.0, self.Vmax - 1.0)
        if self.Umax > self._inf:
            self.Umax = max(1.0, self.Umin + 1.0)
        if self.Vmax > self._inf:
            self.Vmax = max(1.0, self.Vmin + 1.0)

    def _validate_bounds(self):
        "Limit boundaries to basis surface boundaries"
        pr = self.basis_surf.bounds()
        self.Umin = max(pr[0], self.Umin)
        self.Umax = min(pr[1], self.Umax)
        self.Vmin = max(pr[2], self.Vmin)
        self.Vmax = min(pr[3], self.Vmax)

    @property
    def Bounds(self):
        "Parametric limits of the surface"
        return self.Umin, self.Umax, self.Vmin, self.Vmax

    @Bounds.setter
    def Bounds(self, pr):
        if not len(pr) == 4:
            raise ValueError("4 values required : u0, u1, v0, v1")
        self.Umin, self.Umax, self.Vmin, self.Vmax = pr
        self._validate_bounds()

    def extendU(self, *args, **kwargs):
        """
        Extend U bounds, Requires 0,1 or 2 positive values.
        Keyword Relative (bool): values are relative to current U range
        """
        mult = 1.0
        try:
            if kwargs["Relative"]:
                mult = self.Umax - self.Umin
        except KeyError:
            pass
        if len(args) == 0:
            pr = self.basis_surf.bounds()
            if pr[0] > -self._inf:
                self.Umin = pr[0]
            if pr[1] < self._inf:
                self.Umax = pr[1]
        elif len(args) == 1:
            self.Umin -= args[0] * mult
            self.Umax += args[0] * mult
        elif len(args) == 2:
            self.Umin -= args[0] * mult
            self.Umax += args[1] * mult
        self._validate_bounds()

    def extendV(self, *args, **kwargs):
        """
        Extend V bounds, Requires 0,1 or 2 positive values
        Keyword Relative (bool): values are relative to current V range
        """
        mult = 1.0
        try:
            if kwargs["Relative"]:
                mult = self.Vmax - self.Vmin
        except KeyError:
            pass
        if len(args) == 0:
            pr = self.basis_surf.bounds()
            if pr[2] > -self._inf:
                self.Vmin = pr[2]
            if pr[3] < self._inf:
                self.Vmax = pr[3]
        elif len(args) == 1:
            self.Vmin -= args[0] * mult
            self.Vmax += args[0] * mult
        elif len(args) == 2:
            self.Vmin -= args[0] * mult
            self.Vmax += args[1] * mult
        self._validate_bounds()

    def extend(self, *args, **kwargs):
        """
        Extend bounds, Requires 0,1,2 or 4 positive values
        Keyword Relative (bool): values are relative to current param range
        """
        rel = False
        try:
            rel = kwargs["Relative"]
        except KeyError:
            pass
        if len(args) == 0:
            pr = self.basis_surf.bounds()
            if pr[0] > -self._inf:
                self.Umin = pr[0]
            if pr[1] < self._inf:
                self.Umax = pr[1]
            if pr[2] > -self._inf:
                self.Vmin = pr[2]
            if pr[3] < self._inf:
                self.Vmax = pr[3]
        elif len(args) == 1:
            self.extendU(args[0], Relative=rel)
            self.extendV(args[0], Relative=rel)
        elif len(args) == 2:
            self.extendU(args[0], Relative=rel)
            self.extendV(args[1], Relative=rel)
        elif len(args) == 3:
            raise ValueError("0,1,2 or 4 values required")
        elif len(args) == 4:
            self.extendU(*args[:2], Relative=rel)
            self.extendV(*args[2:], Relative=rel)

    @property
    def Surface(self):
        "The resulting trimmed surface"
        rts = Part.RectangularTrimmedSurface(self.basis_surf,
                                             self.Umin, self.Umax,
                                             self.Vmin, self.Vmax)
        return rts

    @property
    def Face(self):
        "The resulting trimmed face"
        return self.Surface.toShape()


