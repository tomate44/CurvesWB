import FreeCAD
import FreeCADGui
import math
from pivy import coin

class gridNode(coin.SoSeparator):
    def __init__(self):
        super(gridNode, self).__init__()

        self.material1 = coin.SoMaterial()
        self.material2 = coin.SoMaterial()
        self.material3 = coin.SoMaterial()
        self.coord = coin.SoCoordinate3()
        self.line1 = coin.SoIndexedLineSet()
        self.line2 = coin.SoIndexedLineSet()
        self.lineSet = coin.SoIndexedLineSet()

        self.addChild(self.coord)
        self.addChild(self.material1)
        self.addChild(self.line1)
        self.addChild(self.material2)
        self.addChild(self.line2)
        self.addChild(self.material3)
        self.addChild(self.lineSet)
        
        self._vector1 = coin.SbVec3f(1,0,0)
        self._vector2 = coin.SbVec3f(0,1,0)
        self.normal = self._vector1.cross(self._vector2)

        self._mainDim = 100
        self._subDim = 10
        self.maxviz = 1.0
        
        self._numGridLines = 4
        self.material1.diffuseColor = coin.SbColor(1,0,0)
        self.material2.diffuseColor = coin.SbColor(0,1,0)
        self.material3.diffuseColor = coin.SbColor(0.5,0.5,0.5)
        self.material3.transparency = 0.5

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

    @property
    def vector1dir(self):
        return self._vector1.getValue()

    @vector1dir.setter
    def vector1dir(self, vec):
        self._vector1 = coin.SbVec3f(vec)
        self.normal = self._vector1.cross(self._vector2)
        self.buildGrid()

    @property
    def vector2dir(self):
        return self._vector2.getValue()

    @vector2dir.setter
    def vector2dir(self, vec):
        self._vector2 = coin.SbVec3f(vec)
        self.normal = self._vector1.cross(self._vector2)
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

    def buildGrid(self):
        n = int(1.0 * self._mainDim / self._subDim)
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
        pts.append(-self._mainDim * self._vector1)
        pts.append( self._mainDim * self._vector1)
        pts.append(-self._mainDim * self._vector2)
        pts.append( self._mainDim * self._vector2)
        for i in fullRange:
            pts.append(i * self._vector2 - self._mainDim * self._vector1)
            pts.append(i * self._vector2 + self._mainDim * self._vector1)
            pts.append(i * self._vector1 - self._mainDim * self._vector2)
            pts.append(i * self._vector1 + self._mainDim * self._vector2)
        self.coord.point.setValues(0,len(pts),pts)
        self._numGridLines = len(fullRange) * 2
        #self.gridcolor = self.gridcolor
        #self.transparency = self.transparency
        a = []
        l = len(pts)-4
        for i in range(l/2):
            a.append(2*i + 4)
            a.append(2*i + 5)
            a.append(-1)
        self.line1.coordIndex.setValue(0)
        self.line1.coordIndex.setValues(0, 3, [0,1,-1])
        self.line2.coordIndex.setValue(0)
        self.line2.coordIndex.setValues(0, 3, [2,3,-1])
        self.lineSet.coordIndex.setValue(0)
        self.lineSet.coordIndex.setValues(0, len(a), a)

class sensorGridNode(gridNode):
    def __init__(self):
        super(sensorGridNode, self).__init__()
        self.factor = 1.0

    def linkTo(self, cam):
        self.sensor = coin.SoFieldSensor(self.updateCB, None)
        self.sensor.setPriority(0)
        self.sensor.attach(cam.orientation)
        
    def unlink(self):
        self.sensor.detach()

    def updateCB(self, *args):
        ori = self.sensor.getTriggerField().getValue()
        lookat = coin.SbVec3f(0, 0, -1)
        viewdir = ori.multVec(lookat)  #ori.getAxisAngle()[0]
        viewdir.normalize()
        self.normal.normalize()
        val = viewdir.dot(self.normal)
        self.transparency = 1 - self.maxviz * math.pow(abs(val),self.factor)

class gridObject:
    def __init__(self, obj):
        obj.Proxy = self

class gridVP:
    def __init__(self, obj ):
        obj.addProperty("App::PropertyDistance",  "Total",         "Size",   "Size of a grid quadrant").Total = '100mm'
        obj.addProperty("App::PropertyDistance",  "Subdivision",   "Size",   "Size of subdivisions").Subdivision = '10mm'
        obj.addProperty("App::PropertyFloat",     "XY_Attenuation", "View",   "XY plane attenuation").XY_Attenuation = 1.0
        obj.addProperty("App::PropertyFloat",     "XZ_Attenuation", "View",   "XZ plane attenuation").XZ_Attenuation = 50.0
        obj.addProperty("App::PropertyFloat",     "YZ_Attenuation", "View",   "YZ plane attenuation").YZ_Attenuation = 50.0
        obj.addProperty("App::PropertyFloat",     "XY_Visibility",  "View",   "XY plane max visibility").XY_Visibility = 1.0
        obj.addProperty("App::PropertyFloat",     "XZ_Visibility",  "View",   "XZ plane max visibility").XZ_Visibility = 0.5
        obj.addProperty("App::PropertyFloat",     "YZ_Visibility",  "View",   "YZ plane max visibility").YZ_Visibility = 0.5
        obj.addProperty("App::PropertyColor",     "GridColor",     "Color",  "Grid Color").GridColor = (0.5,0.5,0.5)
        obj.Proxy = self

    def attach(self, obj):
        self.xy = sensorGridNode()
        self.xy.vector1dir = (1,0,0)
        self.xy.vector1color = (1,0,0)
        self.xy.vector2dir = (0,1,0)
        self.xy.vector2color = (0,1,0)
        self.xy.mainDim = 100
        self.xy.subDim = 10
        self.xy.maxviz = 1.0
    
        self.xz = sensorGridNode()
        self.xz.vector1dir = (1,0,0)
        self.xz.vector1color = (1,0,0)
        self.xz.vector2dir = (0,0,1)
        self.xz.vector2color = (0,0,1)
        self.xz.mainDim = 100
        self.xz.subDim = 10
        self.xz.maxviz = 0.5
    
        self.yz = sensorGridNode()
        self.yz.vector1dir = (0,1,0)
        self.yz.vector1color = (0,1,0)
        self.yz.vector2dir = (0,0,1)
        self.yz.vector2color = (0,0,1)
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

        self.grid = coin.SoSeparator()

        self.grid.addChild(self.xy)
        self.grid.addChild(self.xz)
        self.grid.addChild(self.yz)
        self.sg.addChild(self.grid)

    def onChanged(self, vp, prop):
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

    def onDelete(self, feature, subelements):
        self.sg.removeChild(self.grid)
        return(True)

def main():

    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython","Grid")
    gridObject(obj)
    gridVP(obj.ViewObject)


if __name__ == '__main__':
    main()
