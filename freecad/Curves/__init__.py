import os
import FreeCAD
from .version import __version__

ICONPATH = os.path.join(os.path.dirname(__file__), "resources", "icons")

TOL3D = 1e-7
TOL2D = 1e-9
if hasattr(FreeCAD.Base, "Precision"):
    TOL3D = FreeCAD.Base.Precision.confusion()
    TOL2D = FreeCAD.Base.Precision.parametric(TOL3D)

FreeCAD.__unit_test__ += ["TestCurves"]