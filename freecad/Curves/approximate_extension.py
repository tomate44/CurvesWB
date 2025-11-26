# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "Approximate extension"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Approximate extension for other FeaturePython objects."

import os
import FreeCAD
import FreeCADGui
import Part
from freecad.Curves import _utils
from FreeCAD import Base

# debug = _utils.debug
debug = _utils.doNothing

# ********************************************************
# ************** Approximate extension *******************
# ********************************************************

""" The following class is an extension to a FeaturePython object.
Here is how to use it.
In the file where you define your FeaturePython object :

- import approximate_extension
- in the onChanged method, call the extension onChanged :

    def onChanged(self, fp, prop):
        ...
        if hasattr(fp,"ExtensionProxy"):
            fp.ExtensionProxy.onChanged(fp, prop)

- in the execute method, call the extension's approximate on the output compound :

        if hasattr(obj,"ExtensionProxy"):
            obj.Shape = obj.ExtensionProxy.approximate(obj, my_output_compound)
        else:
            obj.Shape = my_output_compound

- at the creation of the FeaturePython object:
        fpo = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","my_feature_python")
        my_proxy(fpo)
        approximate_extension.ApproximateExtension(fpo)
        fpo.Active = False

"""


class ApproximateExtension:
    def __init__(self, obj):
        ''' Add the properties '''
        debug("\nApproximate extension Init\n")
        obj.addProperty("App::PropertyInteger", "Samples", "ShapeApproximation", "Number of samples").Samples = 100
        obj.addProperty("App::PropertyBool", "Active", "ShapeApproximation", "Use approximation")
        obj.addProperty("App::PropertyInteger", "DegreeMin", "ShapeApproximation", "Minimum degree of the curve").DegreeMin = 3
        obj.addProperty("App::PropertyInteger", "DegreeMax", "ShapeApproximation", "Maximum degree of the curve").DegreeMax = 5
        obj.addProperty("App::PropertyFloat", "ApproxTolerance", "ShapeApproximation", "Approximation tolerance")
        obj.addProperty("App::PropertyEnumeration", "Continuity", "ShapeApproximation", "Desired continuity of the curve").Continuity = ["C0", "C1", "G1", "C2", "G2", "C3", "CN"]
        obj.addProperty("App::PropertyEnumeration", "Parametrization", "ShapeApproximation", "Parametrization type").Parametrization = ["ChordLength", "Centripetal", "Uniform"]
        obj.addProperty("App::PropertyPythonObject", "ExtensionProxy", "ShapeApproximation", "Proxy object of the approximation extension").ExtensionProxy = self
        obj.Parametrization = "ChordLength"
        obj.Continuity = 'C3'
        self.setTolerance(obj)
        obj.Active = False

    def setTolerance(self, obj):
        obj.ApproxTolerance = 1e-3
        if not obj.Shape.isNull():
            obj.ApproxTolerance *= obj.Shape.BoundBox.DiagonalLength

    def approximate(self, obj, input_shape):
        if not obj.Active:
            return input_shape
        pts = False
        input_edges = None
        if isinstance(input_shape, (list, tuple)):
            # debug(isinstance(input_shape[0],Base.Vector))
            if isinstance(input_shape[0], Base.Vector):
                pts = input_shape
            elif isinstance(input_shape[0], Part.Edge):
                input_edges = input_shape
        else:
            input_edges = input_shape.Edges
        edges = list()
        if input_edges:
            for e in input_edges:
                pts = e.discretize(obj.Samples)
                bs = Part.BSplineCurve()
                bs.approximate(Points=pts,
                               DegMin=obj.DegreeMin,
                               DegMax=obj.DegreeMax,
                               Tolerance=obj.ApproxTolerance,
                               Continuity=obj.Continuity,
                               ParamType=obj.Parametrization)
                edges.append(bs.toShape())
            se = Part.sortEdges(edges)
            wires = []
            for el in se:
                if len(el) > 1:
                    wires.append(Part.Wire(el))
                else:
                    wires.append(el[0])
            if len(wires) > 1:
                return Part.Compound(wires)
            else:
                return wires[0]
        elif pts:
            bs = Part.BSplineCurve()
            bs.approximate(Points=pts,
                           DegMin=obj.DegreeMin,
                           DegMax=obj.DegreeMax,
                           Tolerance=obj.ApproxTolerance,
                           Continuity=obj.Continuity,
                           ParamType=obj.Parametrization)
            return bs.toShape()

    def onChanged(self, fp, prop):
        if prop == "Active":
            debug("Approximate : Active changed\n")
            props = ["Samples", "DegreeMin", "DegreeMax", "ApproxTolerance", "Continuity", "Parametrization"]
            mode = 2
            if fp.Active is True:
                mode = 0
            for p in props:
                fp.setEditorMode(p, mode)
        if prop == "DegreeMin":
            if fp.DegreeMin < 1:
                fp.DegreeMin = 1
            elif fp.DegreeMin > fp.DegreeMax:
                fp.DegreeMin = fp.DegreeMax
            debug("Approximate : DegreeMin changed to " + str(fp.DegreeMin))
        if prop == "DegreeMax":
            if fp.DegreeMax < fp.DegreeMin:
                fp.DegreeMax = fp.DegreeMin
            elif fp.DegreeMax > 14:
                fp.DegreeMax = 14
            debug("Approximate : DegreeMax changed to " + str(fp.DegreeMax))
        if prop == "ApproxTolerance":
            if fp.ApproxTolerance < 1e-6:
                fp.ApproxTolerance = 1e-6
            elif fp.ApproxTolerance > 1000.0:
                fp.ApproxTolerance = 1000.0
            debug("Approximate : ApproxTolerance changed to " + str(fp.ApproxTolerance))

# ********************************************************
# **** Part.BSplineCurve.approximate() documentation *****
# ********************************************************

# Replaces this B-Spline curve by approximating a set of points.
# The function accepts keywords as arguments.

# approximate2(Points = list_of_points)

# Optional arguments :

# DegMin = integer (3) : Minimum degree of the curve.
# DegMax = integer (8) : Maximum degree of the curve.
# Tolerance = float (1e-3) : approximating tolerance.
# Continuity = string ('C2') : Desired continuity of the curve.
# Possible values : 'C0','G1','C1','G2','C2','C3','CN'

# LengthWeight = float, CurvatureWeight = float, TorsionWeight = float
# If one of these arguments is not null, the functions approximates the
# points using variational smoothing algorithm, which tries to minimize
# additional criterium:
# LengthWeight*CurveLength + CurvatureWeight*Curvature + TorsionWeight*Torsion
# Continuity must be C0, C1 or C2, else defaults to C2.

# Parameters = list of floats : knot sequence of the approximated points.
# This argument is only used if the weights above are all null.

# ParamType = string ('Uniform','Centripetal' or 'ChordLength')
# Parameterization type. Only used if weights and Parameters above aren't specified.

# Note : Continuity of the spline defaults to C2. However, it may not be applied if
# it conflicts with other parameters ( especially DegMax ).    parametrization
