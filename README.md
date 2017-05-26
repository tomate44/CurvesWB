# FreeCAD Curves and Surfaces WorkBench

![Curves Workbench](https://github.com/tomate44/CurvesWB/raw/master/docFiles/GeomInfo_01.jpg)

This is a python workbench, with a collection of tools for Nurbs curves and surfaces.
I am a very bad programer, and this workbench is full of dirty, crappy code ;-)
Please don't use these tools for any serious work.

How to install :

This workbench can be installed with FreeCAD's addon manager (name : "Curves")

  OR

- go in your personal FreeCAD folder ( usually ~/.FreeCAD on Linux )
- cd ./Mod ( or create this folder if it doesn't exist )
- git clone https://github.com/tomate44/CurvesWB
- start FreeCAD

if you're lucky, you should see a "Curves" workbench in the workbench dropdown list.

Available tools :

- Create a B-Spline curve
![BSplineCurve](https://github.com/tomate44/CurvesWB/raw/master/docFiles/BSplineCurve_01.jpg)
- Create a parametric editable B-Spline curve from a selected edge
![Editable Spline](https://github.com/tomate44/CurvesWB/raw/master/docFiles/Spline_01.jpg)
- Join a set of edges into a single B-Spline curve
- Discretize an edge with various methods
![Discretize](https://github.com/tomate44/CurvesWB/raw/master/docFiles/Discretize_01.jpg)
- Approximate a set of points to a B-Spline curve or surface
![Approximate1](https://github.com/tomate44/CurvesWB/raw/master/docFiles/Approximate_01.jpg)
![Approximate2](https://github.com/tomate44/CurvesWB/raw/master/docFiles/Approximate_02.jpg)
- Create a parametric blending curve between to edges, with up to G2 continuity
![Blend](https://github.com/tomate44/CurvesWB/raw/master/docFiles/BlendCurve_01.jpg)
- Comb Plot tool to visualize the curvature flow of an edge
![Comb Plot](https://github.com/tomate44/CurvesWB/raw/master/docFiles/CombPlot_01.jpg)
- Zebra tool creates zebra stripes environment texture for surface inspection
- Nurbs surface editor to edit a Nurbs surface by moving the control vertices
- Trim tool to cut a face with an edge 
- Geom Info displays information in the 3D view, about the selected edge or surface
![Geom Info 1](https://github.com/tomate44/CurvesWB/raw/master/docFiles/GeomInfo_01.jpg)
![Geom Info 2](https://github.com/tomate44/CurvesWB/raw/master/docFiles/GeomInfo_02.jpg)
- Extract subShapes from an object
- Parametric isocurve object
- Map a sketch on a face
- Birail object to be used as support for a "Sweep On 2 Rails" tool

LGPL2+ license
