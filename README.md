# FreeCAD Curves and Surfaces WorkBench

This is a python workbench, with a collection of tools for Nurbs curves and surfaces.
I am a very bad programer, and this workbench is full of dirty, crappy code ;-)

If ever you want to try it anyway, go in your personal FreeCAD folder ( usually ~/.FreeCAD on Linux ) :
- cd ./Mod ( or create this folder if it doesn't exist )
- git clone https://github.com/tomate44/CurvesWB
- start FreeCAD
- if you're lucky, you should see a "Curves" workbench in the workbench dropdown list.

This workbench can also be installed with FreeCAD's addon manager (name : "Curves")

Available tools :

![Create a B-Spline curve](https://github.com/tomate44/CurvesWB/blob/master/Resources/icons/bezier.svg?raw=true)   
- Blend Curve : creates a parametric blend curve between 2 input edges, with G2 continuity
- Comb Plot : creates a parametric comb plot for input edges, to visualize edge curvature
- Zebra Tool : creates zebra stripes environment texture for surface inspection
- Nurbs surface editor : to edit a Nurbs surface by moving the control vertices
- Info : displays information in the 3D view, about the selected edge or surface

LGPL2+ license
