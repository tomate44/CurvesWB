#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 - Christophe Grellier (Chris_G)                    *
#*                                                                         *  
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__="Macro IsoCurves"
__author__ = "Chris_G"
__doc__ = '''
Macro IsoCurves.
Creates a parametric isoCurve from a face

Instructions:
Select a face in the 3D View.
Then, in Py console:

import IsoCurves
IsoCurves.run()

'''
import os, dummy
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui

import Part

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')


def makeIsoCurveFeature():
    '''makeIsoCurveFeature(): makes a IsoCurve parametric feature object. Returns the new object.'''
    selfobj = App.ActiveDocument.addObject("Part::FeaturePython","IsoCurve")
    IsoCurve(selfobj)
    ViewProviderIsoCurve(selfobj.ViewObject)
    return selfobj

class IsoCurve:
    "The IsoCurve feature object"
    def __init__(self,selfobj):
        selfobj.addProperty("App::PropertyLinkSub","Face","IsoCurve","Input face")
        selfobj.addProperty("App::PropertyFloat","Parameter","IsoCurve","IsoCurve parameter").Parameter=50.
        selfobj.addProperty("App::PropertyEnumeration","Orientation","IsoCurve","Curve Orientation").Orientation=["U","V"]
        selfobj.Proxy = self

    def execute(self,selfobj):
        
        #if len(selfobj.Base.Shape.Faces) == 0 or len(selfobj.Tool.Shape.Faces) == 0:
            #raise ValueError("Shapes must have at least one face each.")
        n = eval(selfobj.Face[1][0].lstrip('Face'))
        face = selfobj.Face[0].Shape.Faces[n-1]
        u0,u1,v0,v1 = face.Surface.bounds()
        if selfobj.Orientation == 'U':
            uRange = u1-u0
            iso = face.Surface.uIso(u0 + 1.*selfobj.Parameter*uRange / 100.0)
        elif selfobj.Orientation == 'V':
            vRange = v1-v0
            iso = face.Surface.vIso(v0 + 1.*selfobj.Parameter*vRange / 100.0)        
        selfobj.Shape = iso.toShape()

    def onChanged(self, selfobj, prop):
        if prop == 'Parameter':
            if   selfobj.Parameter  < 0.0:
                 selfobj.Parameter  = 0.0
            elif selfobj.Parameter  > 100.0:
                 selfobj.Parameter  = 100.0
            selfobj.Proxy.execute(selfobj)
        if prop == 'Orientation':
            selfobj.Proxy.execute(selfobj)

class ViewProviderIsoCurve:
    def __init__(self,vobj):
        vobj.Proxy = self
       
    def getIcon(self):
        return (path_curvesWB_icons+'/isocurve.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
  
    def setEdit(self,vobj,mode):
        return False
    
    def unsetEdit(self,vobj,mode):
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

    #def claimChildren(self):
        #return None #[self.Object.Base, self.Object.Tool]
        
    def onDelete(self, feature, subelements): # subelements is a tuple of strings
        #try:
            #self.Object.Base.ViewObject.show()
            #self.Object.Tool.ViewObject.show()
        #except Exception as err:
            #App.Console.PrintError("Error in onDelete: " + err.message)
        return True

class CommandMacroIsoCurve:
    "Command to create IsoCurve feature"
    def GetResources(self):
        return {'Pixmap'  : path_curvesWB_icons+'/isocurve.svg',
                'MenuText': "IsoCurve",
                'Accel': "",
                'ToolTip': "IsoCurve: Create an IsoCurve from a face"}

    def Activated(self):
        run()
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

if App.GuiUp:
    Gui.addCommand("IsoCurve", CommandMacroIsoCurve())

def run():
    sel = Gui.Selection.getSelectionEx()
    try:
        if len(sel) != 1:
            raise Exception("Select one face only.")
        try:
            App.ActiveDocument.openTransaction("Macro IsoCurve")
            selfobj = makeIsoCurveFeature()
            selfobj.Face = [sel[0].Object,sel[0].SubElementNames]
            # set parameter here
            selfobj.Proxy.execute(selfobj)
        finally:
            App.ActiveDocument.commitTransaction()
    except Exception as err:
        from PySide import QtGui
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText(err.message)
        mb.setWindowTitle("Macro IsoCurve")
        mb.exec_()
