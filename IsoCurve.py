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
        selfobj.addProperty("App::PropertyFloat","Parameter","IsoCurve","IsoCurve parameter").Parameter=0.
        selfobj.addProperty("App::PropertyEnumeration","Orientation","IsoCurve","Curve Orientation").Orientation=["U","V"]
        selfobj.Proxy = self

    def split(self, e, t0, t1):
        p0,p1 = e.ParameterRange
        if (t0 > p0) & (t1 < p1):
            w = e.split([t0,t1])
            return w.Edges[1]
        elif (t0 > p0):
            w = e.split(t0)
            return w.Edges[1]
        elif (t1 < p1):
            w = e.split(t1)
            return w.Edges[0]
        else:
            return e

    def getBounds(self, obj):
        face = self.getFace(obj)
        self.u0, self.u1, self.v0, self.v1 = face.ParameterRange

    def getFace(self, obj):
        try:
            n = eval(obj.Face[1][0].lstrip('Face'))
            face = obj.Face[0].Shape.Faces[n-1]
            #self.u0, self.u1, self.v0, self.v1 = self.face.ParameterRange
            return face
        except:
            return None

    def tangentAt(self, selfobj, p):
        if selfobj.Orientation == 'U':
            if (p >= self.v0) & (p <= self.v1):
                return selfobj.Shape.tangentAt(p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n"%(self.v0,self.v1))
        if selfobj.Orientation == 'V':
            if (p >= self.u0) & (p <= self.u1):
                return selfobj.Shape.tangentAt(p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n"%(self.u0,self.u1))

    def normalAt(self, selfobj, p):
        face = self.getFace(selfobj)
        if selfobj.Orientation == 'U':
            if (p >= self.v0) & (p <= self.v1):
                return face.normalAt(selfobj.Parameter, p)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n"%(self.v0,self.v1))
        if selfobj.Orientation == 'V':
            if (p >= self.u0) & (p <= self.u1):
                return face.normalAt(p, selfobj.Parameter)
            else:
                App.Console.PrintError("Parameter out of range (%f, %f)\n"%(self.u0,self.u1))

    def execute(self,selfobj):

        face = self.getFace(selfobj)
        #u0,u1,v0,v1 = face.ParameterRange
        if face:
            if selfobj.Orientation == 'U':
                iso = face.Surface.uIso(selfobj.Parameter)
                e = Part.Edge(iso)
                w = self.split(e,self.v0,self.v1)
            elif selfobj.Orientation == 'V':
                iso = face.Surface.vIso(selfobj.Parameter) 
                e = Part.Edge(iso)
                w = self.split(e,self.u0,self.u1)
            selfobj.Shape = w
        else:
            return False

    def onChanged(self, selfobj, prop):
        if prop == 'Face':
            face = self.getFace(selfobj)
            self.getBounds(selfobj)
            if selfobj.Orientation == "U":
                self.p0 = self.u0
                self.p1 = self.u1
            else:
                self.p0 = self.v0
                self.p1 = self.v1
        if prop == 'Parameter':
            if   selfobj.Parameter  < self.p0:
                 selfobj.Parameter  = self.p0
            elif selfobj.Parameter  > self.p1:
                 selfobj.Parameter  = self.p1
            selfobj.Proxy.execute(selfobj)
        if prop == 'Orientation':
            self.getBounds(selfobj)
            if selfobj.Orientation == "U":
                self.p0 = self.u0
                self.p1 = self.u1
            else:
                self.p0 = self.v0
                self.p1 = self.v1
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
            so = sel[0].SubObjects[0]
            p = sel[0].PickedPoints[0]
            poe = so.distToShape(Part.Vertex(p))
            par = poe[2][0][2]
            selfobj.Face = [sel[0].Object,sel[0].SubElementNames]
            selfobj.Parameter = par[0]
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
