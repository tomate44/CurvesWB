# FreeCAD Curves and Surfaces WorkBench

![Curves Workbench](https://github.com/tomate44/CurvesWB/raw/master/docFiles/GeomInfo_01.jpg)

This is a python workbench, with a collection of tools for NURBS curves and surfaces. This workbench is developed with FreeCAD Master (currently 0.17dev) and OCC 7.1. 
Some tools may not work with earlier versions.

**Note:** I am a very bad programer, and this workbench is full of dirty, crappy code ;-) Please don't use these tools for any serious work.

## Installation 
There are 2 methods to install Curves WB:
1. For FreeCAD version 0.17 or higher it's preferred to install this workbench with the [FreeCAD's addon manager](https://github.com/FreeCAD/FreeCAD-addons) under the label "Curves".  
2. The second method is 
- go in your personal FreeCAD folder ( usually ~/.FreeCAD on Linux )
- cd ./Mod ( or create this folder if it doesn't exist )
- git clone https://github.com/tomate44/CurvesWB
- start FreeCAD

"Curves" workbench should now show up in the workbench dropdown list.

## Feedback  
Feedback, suggestions, and patches (via Pull Request) are all appreciated. If you find a problem with this workbench please open an issue in the issue queue. 
 

## Curves WB Tools 
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

## License  
CurvesWB is released under the LGPL2+ license
