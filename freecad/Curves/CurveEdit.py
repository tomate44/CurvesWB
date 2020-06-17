import os
import FreeCAD, FreeCADGui, Part
from pivy import coin
import CoinNodes
import HUD
import dummy

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

class curveEdit:
    def __init__(self, edge):
        pass
 

def main():
    doc = FreeCAD.ActiveDocument
    bs = Part.BSplineCurve()
    edge = Part.Edge(bs)
    curveEdit(edge)

if __name__ == '__main__':
    main()

