# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import math
from pivy import coin

# -------- Example of the gridNode object

#import grid

#g = grid.gridNode()
#sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
#cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()

#sg.addChild(g)
#g.linkTo(cam)
#g.factor = 1.
#g.maxviz = 1.0
#g.vector1dir = (1,0,0)
#g.vector2dir = (0,1,0)
#g.factor = 100.0

##sg.removeChild(g)


class gridNode(coin.SoSeparator):
    def __init__(self):
        super(gridNode, self).__init__()

        self.vec = coin.SoTransformVec3f()
        #self.vec.matrix.connectFrom(cam.orientation)
        self.vec.vector = coin.SbVec3f(0,0,-1)

        self.calc = coin.SoCalculator()
        self.calc.A.connectFrom(self.vec.direction)
        self.calc.expression.set1Value(0,"ta=0.5") # maxviz
        self.calc.expression.set1Value(1,"tb=20.0") # factor
        self.calc.expression.set1Value(2,"tA=vec3f(1,0,0)") # plane normal
        self.calc.expression.set1Value(3,"tc=dot(A,tA)")
        self.calc.expression.set1Value(4,"td=fabs(tc)")
        self.calc.expression.set1Value(5,"oa=1.0-ta*pow(td,tb)")
        self.calc.expression.set1Value(6,"oA=vec3f(oa,0,0)")

        self.scaleEngine = coin.SoCalculator()
        #self.scaleEngine.a.connectFrom(cam.height)
        self.scaleEngine.expression.set1Value(0,"ta=floor(log10(a/10))")
        self.scaleEngine.expression.set1Value(1,"tb=pow(10,ta)")
        self.scaleEngine.expression.set1Value(2,"oA=vec3f(tb,tb,tb)")
        self.scaleEngine.expression.set1Value(3,"oa=0.01*a/tb")

        self.calc2 = coin.SoCalculator()
        self.calc2.a.connectFrom(self.scaleEngine.oa)
        self.calc2.b.connectFrom(self.calc.oa)
        self.calc2.expression.set1Value(0,"ta=pow(a,0.3)")
        self.calc2.expression.set1Value(1,"oa=(b>ta)?b:ta")


        self.material1 = coin.SoMaterial()
        self.material2 = coin.SoMaterial()
        self.material3 = coin.SoMaterial()
        self.material4 = coin.SoMaterial()
        self.coord = coin.SoCoordinate3()
        self.coord2= coin.SoCoordinate3()
        self.line1 = coin.SoIndexedLineSet()
        self.line2 = coin.SoIndexedLineSet()
        self.lineSet = coin.SoIndexedLineSet()
        self.lineSet2= coin.SoIndexedLineSet()

        self.miniscale = coin.SoScale()
        self.miniscale.scaleFactor = coin.SbVec3f(0.1,0.1,0.1)

        self.mainscale = coin.SoScale()
        self.mainscale.scaleFactor.connectFrom(self.scaleEngine.oA)

        self.addChild(self.mainscale)
        self.addChild(self.coord)
        self.addChild(self.material1)
        self.addChild(self.line1)
        self.addChild(self.material2)
        self.addChild(self.line2)
        self.addChild(self.material3)
        self.addChild(self.lineSet)
        self.addChild(self.miniscale)
        self.addChild(self.material4)
        self.addChild(self.coord2)
        self.addChild(self.lineSet2)
       
        self._vector1 = coin.SbVec3f(1,0,0)
        self._vector2 = coin.SbVec3f(0,1,0)
        self.normal = self._vector1.cross(self._vector2)

        self._mainDim = 100
        self._subDim = 10
        self._maxviz = 1.0
        self._factor = 1.0
       
        self._numGridLines = 4
        self.material1.diffuseColor = coin.SbColor(1,0,0)
        self.material2.diffuseColor = coin.SbColor(0,1,0)
        self.material3.diffuseColor = coin.SbColor(0.5,0.5,0.5)
        self.material4.diffuseColor = coin.SbColor(0.5,0.5,0.5)
        self.material3.transparency.connectFrom(self.calc.oa)
        self.material4.transparency.connectFrom(self.calc2.oa)


    @property
    def transparency(self):
        return self.material3.transparency.getValues()[0]

    @transparency.setter
    def transparency(self, tr):
#        self.material3.transparency = tr
#        self.material2.transparency = tr
        self.material3.transparency = tr

    @property
    def vector1color(self):
        return self.material1.diffuseColor.getValues()[0].getValue()

    @vector1color.setter
    def vector1color(self, color):
        self.material1.diffuseColor = (color[0], color[1], color[2])

    @property
    def vector2color(self):
        return self.material2.diffuseColor.getValues()[0].getValue()

    @vector2color.setter
    def vector2color(self, color):
        self.material2.diffuseColor = (color[0], color[1], color[2])

    @property
    def gridcolor(self):
        return self.material3.diffuseColor.getValues()[0].getValue()

    @gridcolor.setter
    def gridcolor(self, color):
        self.material3.diffuseColor = (color[0], color[1], color[2])
        self.material4.diffuseColor = (color[0], color[1], color[2])

    @property
    def vector1dir(self):
        return self._vector1.getValue()

    @vector1dir.setter
    def vector1dir(self, vec):
        self._vector1 = coin.SbVec3f(vec)
        self.normal = self._vector1.cross(self._vector2)
        self.calc.expression.set1Value(2,"tA=vec3f(%f,%f,%f)"%(self.normal.getValue()[0],self.normal.getValue()[1],self.normal.getValue()[2]))
        self.buildGrid()

    @property
    def vector2dir(self):
        return self._vector2.getValue()

    @vector2dir.setter
    def vector2dir(self, vec):
        self._vector2 = coin.SbVec3f(vec)
        self.normal = self._vector1.cross(self._vector2)
        self.calc.expression.set1Value(2,"tA=vec3f(%f,%f,%f)"%(self.normal.getValue()[0],self.normal.getValue()[1],self.normal.getValue()[2]))
        self.buildGrid()

    @property
    def mainDim(self):
        return self._mainDim

    @mainDim.setter
    def mainDim(self, n):
        self._mainDim = n
        self.buildGrid()
       
    @property
    def subDim(self):
        return self._subDim

    @subDim.setter
    def subDim(self, n):
        self._subDim = n
        self.buildGrid()

    @property
    def maxviz(self):
        return self._maxviz

    @maxviz.setter
    def maxviz(self, n):
        self._maxviz = n
        self.calc.expression.set1Value(0,"ta=%f"%n) # maxviz

    @property
    def factor(self):
        return self._factor

    @factor.setter
    def factor(self, n):
        self._factor = n
        self.calc.expression.set1Value(1,"tb=%f"%n) # factor

    def linkTo(self, cam):
        self.vec.matrix.connectFrom(cam.orientation)
        self.scaleEngine.a.connectFrom(cam.height)

    def updateTransformedNormal(self):
#          // First get hold of an SoPath through the scenegraph down to the
#          // node ("mynode") you want to query about its current world space
#          // transformation(s).
#        
#          SoSearchAction * searchaction = new SoSearchAction;
#          searchaction->setNode(mynode);
#          searchaction->apply(myscenegraphroot);
#        
#          SoPath * path = searchaction->getPath();
#          assert(path != NULL);
#        
#          // Then apply the SoGetMatrixAction to get the full transformation
#          // matrix from world space.
#        
#          const SbViewportRegion vpr = myviewer->getViewportRegion();
#          SoGetMatrixAction * getmatrixaction = new SoGetMatrixAction(vpr);
#          getmatrixaction->apply(path);
#        
#          SbMatrix transformation = getmatrixaction->getMatrix();
#        
#          // And if you want to access the individual transformation
#          // components of the matrix:
#        
#          SbVec3f translation;
#          SbRotation rotation;
#          SbVec3f scalevector;
#          SbRotation scaleorientation;
#        
#          transformation.getTransform(translation, rotation, scalevector, scaleorientation);
        searchaction = coin.SoSearchAction()
        searchaction.setNode(self)
        searchaction.apply(FreeCADGui.ActiveDocument.ActiveView.getSceneGraph())
        path = searchaction.getPath()
        vpr = FreeCADGui.ActiveDocument.ActiveView.getViewer().getViewportRegion()
        getmatrixaction = coin.SoGetMatrixAction(vpr)
        getmatrixaction.apply(path)
        transformation = getmatrixaction.getMatrix()
        self.transformedNormal = transformation.multVecMatrix(self.normal)
        self.calc.expression.set1Value(2,"tA=vec3f(%f,%f,%f)"%(self.transformedNormal.getValue()[0],self.transformedNormal.getValue()[1],self.transformedNormal.getValue()[2]))
        return()

    def gridPts(self, t, s):
        n = t*s
        r = []
        nr = []
        for i in range(1,n):
            r.append(  1.0 * self._subDim * i)
            nr.append(-1.0 * self._subDim * i)
        r.append(  self._mainDim)
        nr.append(-self._mainDim)
        nr.reverse()
        fullRange = nr + r
        pts = []
        for i in fullRange:
            pts.append(1*i * self._vector2 - s*self._mainDim * self._vector1)
            pts.append(1*i * self._vector2 + s*self._mainDim * self._vector1)
            pts.append(1*i * self._vector1 - s*self._mainDim * self._vector2)
            pts.append(1*i * self._vector1 + s*self._mainDim * self._vector2)
        return(pts)

    def buildGrid(self):
        n = int(1.0 * self._mainDim / self._subDim)
        
        pts = []
        pts.append(-self._mainDim * self._vector1)
        pts.append( self._mainDim * self._vector1)
        pts.append(-self._mainDim * self._vector2)
        pts.append( self._mainDim * self._vector2)
        
        pts += self.gridPts(n,1)
        self.coord.point.setValues(0,len(pts),pts)
        self._numGridLines = len(pts) / 2.0

        pts2 = self.gridPts(n,10)
        self.coord2.point.setValues(0,len(pts2),pts2)
        #self._numGridLines = len(pts) / 2.0

        a = []
        l = len(pts)-4
        for i in range(int(l/2)):
            a.append(2*i + 4)
            a.append(2*i + 5)
            a.append(-1)
        self.line1.coordIndex.setValue(0)
        self.line1.coordIndex.setValues(0, 3, [0,1,-1])
        self.line2.coordIndex.setValue(0)
        self.line2.coordIndex.setValues(0, 3, [2,3,-1])
        self.lineSet.coordIndex.setValue(0)
        self.lineSet.coordIndex.setValues(0, len(a), a)

        a2 = []
        l = len(pts2)
        for i in range(int(l/2)):
            a2.append(2*i)
            a2.append(2*i + 1)
            a2.append(-1)
        self.lineSet2.coordIndex.setValue(0)
        self.lineSet2.coordIndex.setValues(0, len(a2), a2)


class gridObject:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyPlacement",  "Placement",   "Base",   "Placement")
    def execute(self, obj):
        return()
    def onChanged(self, fp, prop):
        if prop == 'Placement':
            FreeCAD.Console.PrintMessage('Placement update\n')
            tr = fp.Placement.Base
            ro = fp.Placement.Rotation.Q
            fp.ViewObject.Proxy.trans.translation = coin.SbVec3f(tr.x,tr.y,tr.z)
            fp.ViewObject.Proxy.trans.rotation = coin.SbRotation(ro[0],ro[1],ro[2],ro[3])
    

class gridVP:
    def __init__(self, obj ):
        obj.addProperty("App::PropertyDistance",  "Total",         "Size",   "Size of a grid quadrant").Total = '100mm'
        obj.addProperty("App::PropertyDistance",  "Subdivision",   "Size",   "Size of subdivisions").Subdivision = '10mm'
        obj.addProperty("App::PropertyFloat",     "XY_Attenuation", "View",   "XY plane attenuation").XY_Attenuation = 2.0
        obj.addProperty("App::PropertyFloat",     "XZ_Attenuation", "View",   "XZ plane attenuation").XZ_Attenuation = 50.0
        obj.addProperty("App::PropertyFloat",     "YZ_Attenuation", "View",   "YZ plane attenuation").YZ_Attenuation = 50.0
        obj.addProperty("App::PropertyFloat",     "XY_Visibility",  "View",   "XY plane max visibility").XY_Visibility = 1.0
        obj.addProperty("App::PropertyFloat",     "XZ_Visibility",  "View",   "XZ plane max visibility").XZ_Visibility = 0.5
        obj.addProperty("App::PropertyFloat",     "YZ_Visibility",  "View",   "YZ plane max visibility").YZ_Visibility = 0.5
        obj.addProperty("App::PropertyColor",     "GridColor",     "Color",  "Grid Color").GridColor = (0.5,0.5,0.5)
        obj.Proxy = self

    def attach(self, obj):

        self.trans = coin.SoTransform()

        self.xy = gridNode()
        self.xy.vector1dir = (1,0,0)
        self.xy.vector1color = (0.827,0.149,0.149) # red (X)
        self.xy.vector2dir = (0,1,0)
        self.xy.vector2color = (0.400,0.590,0.200) # green (Y)
        self.xy.mainDim = 100
        self.xy.subDim = 10
        self.xy.maxviz = 1.0
   
        self.xz = gridNode()
        self.xz.vector1dir = (1,0,0)
        self.xz.vector1color = (0.827,0.149,0.149) # red (X)
        self.xz.vector2dir = (0,0,1)
        self.xz.vector2color = (0.133,0.490,0.882) # blue (Z)
        self.xz.mainDim = 100
        self.xz.subDim = 10
        self.xz.maxviz = 0.5
   
        self.yz = gridNode()
        self.yz.vector1dir = (0,1,0)
        self.yz.vector1color = (0.400,0.590,0.200) # green (Y)
        self.yz.vector2dir = (0,0,1)
        self.yz.vector2color = (0.133,0.490,0.882) # blue (Z)
        self.yz.mainDim = 100
        self.yz.subDim = 10
        self.yz.maxviz = 0.5
   
        self.sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
        self.cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
   
        self.xy.linkTo(self.cam)
        self.xy.factor = 1.
        self.xz.linkTo(self.cam)
        self.xz.factor = 50.
        self.yz.linkTo(self.cam)
        self.yz.factor = 50.

        self.grid = coin.SoGroup()

        self.grid.addChild(self.trans)
        self.grid.addChild(self.xy)
        self.grid.addChild(self.xz)
        self.grid.addChild(self.yz)
        obj.addDisplayMode(self.grid,"Wireframe")

        self.ViewObject = obj
        self.Object = obj.Object

#    def updateCam(self):
#        self.cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
#        self.xy.linkTo(self.cam)
#        self.xz.linkTo(self.cam)
#        self.yz.linkTo(self.cam)

    def getIcon(self):
        return (":/icons/Draft_Grid.svg")

    def getDisplayModes(self,obj):
         "Return a list of display modes."
         modes=[]
         modes.append("Wireframe")
         return modes

    def getDefaultDisplayMode(self):
         "Return the name of the default display mode. It must be defined in getDisplayModes."
         return "Wireframe"

    def setDisplayMode(self,mode):
         return mode

    def updateCam(self):
        self.cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
        self.xy.linkTo(self.cam)
        self.xz.linkTo(self.cam)
        self.yz.linkTo(self.cam)

    def onChanged(self, vp, prop):
        self.updateCam()
        if prop == 'Total':
            if float(vp.Total) >= float(vp.Subdivision):
                self.xy.mainDim = float(vp.Total)
                self.xz.mainDim = float(vp.Total)
                self.yz.mainDim = float(vp.Total)
            else:
                vp.Total = vp.Subdivision
        if prop == 'Subdivision':
            if float(vp.Total) >= float(vp.Subdivision):
                self.xy.subDim = float(vp.Subdivision)
                self.xz.subDim = float(vp.Subdivision)
                self.yz.subDim = float(vp.Subdivision)
            else:
                vp.Subdivision = vp.Total
        if prop == 'XY_Attenuation':
            if vp.XY_Attenuation < 0.1:
                vp.XY_Attenuation = 0.1
            elif vp.XY_Attenuation > 100:
                vp.XY_Attenuation = 100
            self.xy.factor = vp.XY_Attenuation
        if prop == 'XZ_Attenuation':
            if vp.XZ_Attenuation < 0.1:
                vp.XZ_Attenuation = 0.1
            elif vp.XZ_Attenuation > 100:
                vp.XZ_Attenuation = 100
            self.xz.factor = vp.XZ_Attenuation
        if prop == 'YZ_Attenuation':
            if vp.YZ_Attenuation < 0.1:
                vp.YZ_Attenuation = 0.1
            elif vp.YZ_Attenuation > 100:
                vp.YZ_Attenuation = 100
            self.yz.factor = vp.YZ_Attenuation
        if prop == 'XY_Visibility':
            if vp.XY_Visibility < 0.0:
                vp.XY_Visibility = 0.0
            elif vp.XY_Visibility > 1.0:
                vp.XY_Visibility = 1.0
            self.xy.maxviz = vp.XY_Visibility
        if prop == 'XZ_Visibility':
            if vp.XZ_Visibility < 0.0:
                vp.XZ_Visibility = 0.0
            elif vp.XZ_Visibility > 1.0:
                vp.XZ_Visibility = 1.0
            self.xz.maxviz = vp.XZ_Visibility
        if prop == 'YZ_Visibility':
            if vp.YZ_Visibility < 0.0:
                vp.YZ_Visibility = 0.0
            elif vp.YZ_Visibility > 1.0:
                vp.YZ_Visibility = 1.0
            self.yz.maxviz = vp.YZ_Visibility
        if prop == 'GridColor':
            self.xy.gridcolor = vp.GridColor
            self.xz.gridcolor = vp.GridColor
            self.yz.gridcolor = vp.GridColor
        if prop == 'Placement':
            FreeCAD.Console.PrintMessage('Placement update\n')
            tr = vp.Object.Placement.Base
            ro = vp.Object.Placement.Rotation.Q
            self.trans.translation = coin.SbVec3f(tr.x,tr.y,tr.z)
            self.trans.rotation = coin.SbRotation(ro[0],ro[1],ro[2],ro[3])
            self.xy.updateTransformedNormal()
            self.xz.updateTransformedNormal()
            self.yz.updateTransformedNormal()


    def onDelete(self, feature, subelements):
        self.sg.removeChild(self.grid)
        return(True)

def main():

    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Grid")
    gridObject(obj)
    gridVP(obj.ViewObject)


if __name__ == '__main__':
    main()

