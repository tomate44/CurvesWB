# SPDX-License-Identifier: LGPL-2.1-or-later

from math import pi
from pivy import coin
import Part


def getPoint(pX,pY):
    render_manager = Gui.ActiveDocument.ActiveView.getViewer().getSoRenderManager()
    cam = render_manager.getCamera()
    ws = render_manager.getWindowSize().getValue()
    ar = 1.0 * ws[0] / ws[1]
    vol = cam.getViewVolume()
    line = coin.SbLine(*vol.projectPointToLine(coin.SbVec2f(pX*ar-0.5,pY)))
    normal = coin.SbVec3f(0,0,1)
    center = coin.SbVec3f(0,0,0)
    plane = coin.SbPlane(normal, center)
    point = plane.intersect(line)
    return(FreeCAD.Vector(point.getValue()))


def draw_box():
    #pts = [getPoint(-0.5,-0.5), getPoint(0.5,-0.5), getPoint(0.5,0.5), getPoint(-0.5,0.5), getPoint(-0.5,-0.5)]
    pts = [getPoint(0,0), getPoint(1,0), getPoint(1,1), getPoint(0,1), getPoint(0,0)]
    poly = Part.makePolygon(pts)
    Part.show(poly)


class gridView(coin.SoSeparator):
    def __init__(self, name = "GridView"):
        super(gridView, self).__init__()
        self.setName(name)
        self._number_of_points = 50
        self._center = (0,0)
        self._scale = 1.0
        self._axis = 0 # 1=X 2=Y 3=Z
        self.transform = coin.SoTransform()
        self.coord = coin.SoCoordinate3()
        self.sep1 = coin.SoSeparator()
        self.sep1.setName("Snap_Points")
        self.sep2 = coin.SoSeparator()
        self.sep2.setName("Grid")
        self.sep3 = coin.SoSeparator()
        self.sep3.setName("Axis")
        self.addChild(self.transform)
        self.addChild(self.coord)
        self.addChild(self.sep1)
        self.addChild(self.sep2)
        self.addChild(self.sep3)
        
        ps = coin.SoPointSet()
        ds = coin.SoDrawStyle()
        ds.pointSize = 1
        self.sep1.addChild(ds)
        self.sep1.addChild(ps)
        
        self.color1 = (0.82, 0.15, 0.15) # red (X)
        self.color2 = (0.40, 0.59, 0.20) # green (Y)
        self.color3 = (0.13, 0.49, 0.88) # blue (Z)

    @property
    def axis(self):
        return(self._axis)

    @axis.setter
    def axis(self, ax):
        if ax == 1:
            self.vector1color = self.color2
            self.vector2color = self.color3
            rot = coin.SoRotationXYZ()
            rot.axis = 1 # rotate around Y
            rot.angle = 0.5 * pi
            self.transform.rotation.setValue(rot.getRotation())
            self._axis = 1
        elif ax == 2:
            self.vector1color = self.color1
            self.vector2color = self.color3
            rot = coin.SoRotationXYZ()
            rot.axis = 0 # rotate around X
            rot.angle = 0.5 * pi
            self.transform.rotation.setValue(rot.getRotation())
            self._axis = 2
        elif ax == 3:
            self.vector1color = self.color1
            self.vector2color = self.color2
            rot = coin.SoRotationXYZ()
            self.transform.rotation.setValue(rot.getRotation())
            self._axis = 3
        else:
            self._axis = 0

    @property
    def scale(self):
        return(self._scale)

    @scale.setter
    def scale(self, s):
        self._scale = s
        if s == 0:
            self._scale = 1.0
        self.transform.scaleFactor.setValue(coin.SbVec3f(self._scale, self._scale, self._scale))

    def build_lines(self):
        np = self._number_of_points
        n = 1 + 2 * np
        
        self.line_mat1 = coin.SoMaterial()
        ol = list() #[(0.2,0.2,0.2)] + [(0.6,0.6,0.6)] * 9
        bind1 = coin.SoMaterialBinding()
        bind1.value = coin.SoMaterialBinding.PER_PART
        l1 = coin.SoIndexedLineSet()
        l1.coordIndex.setValue(0)
        ind = list()
        for i in range(2 * self._number_of_points + 1):
            if not i == self._number_of_points:
                ind.append((i * n))
                ind.append(((i+1) * n)-1)
                ind.append(-1)
                if (i % 10) == 0:
                    ol.append((0.2,0.2,0.2))
                else:
                    ol.append((0.4,0.4,0.4))
            #print(ind)
        self.line_mat1.diffuseColor.setValues(0, len(ol), ol )
        l1.coordIndex.setValues(0, len(ind), ind)
        
        l2 = coin.SoIndexedLineSet()
        l2.coordIndex.setValue(0)
        ind2 = list()
        for i in range(2 * self._number_of_points + 1):
            if not i == self._number_of_points:
                ind2.append(i)
                ind2.append(i+(n-1)*n)
                ind2.append(-1)
                #if (i % 10) == 0:
                    #ol.append((0.2,0.2,0.2))
                #else:
                    #ol.append((0.4,0.4,0.4))
            #print(ind)
        #self.line_mat1.diffuseColor.setValues(0, len(ol), ol )
        l2.coordIndex.setValues(0, len(ind2), ind2)
        
        
        self.sep2.addChild(bind1)
        self.sep2.addChild(self.line_mat1)
        self.sep2.addChild(l1)
        self.sep2.addChild(l2)

    def build_points(self):
        pts = list()
        sc = 1. / self._number_of_points
        for i in range(-self._number_of_points, self._number_of_points + 1):
            for j in range(-self._number_of_points,self._number_of_points + 1):
                pts.append(coin.SbVec3f(sc * i, sc * j, 0))
        self.coord.point.setValues(0, len(pts), pts)

    def build_axis(self):
        np = self._number_of_points
        n = 1 + 2 * np
        
        ds = coin.SoDrawStyle()
        ds.lineWidth = 2
        self.sep3.addChild(ds)
        
        self.mat1 = coin.SoMaterial()
        #bind1 = coin.SoMaterialBinding()
        #bind1.value = coin.SoMaterialBinding.PER_PART
        ax = coin.SoIndexedLineSet()
        ax.coordIndex.setValue(0)
        ax.coordIndex.setValues(0, 3, [n*np, n*(np+1)-1, -1])
        #self.sep3.addChild(bind1)
        self.sep3.addChild(self.mat1)
        self.sep3.addChild(ax)
        
        self.mat2 = coin.SoMaterial()
        #bind2 = coin.SoMaterialBinding()
        #bind2.value = coin.SoMaterialBinding.PER_PART
        ax2 = coin.SoIndexedLineSet()
        ax2.coordIndex.setValue(0)
        ax2.coordIndex.setValues(0, 3, [np, n*(n-1) + np, -1])
        #self.sep3.addChild(bind2)
        self.sep3.addChild(self.mat2)
        self.sep3.addChild(ax2)


class orthoToggleSwitch(coin.SoSwitch):
    def __init__(self, name = "ToggleSwitch", cam = None):
        super(orthoToggleSwitch, self).__init__()

        self.setName(name)

        self.vec = coin.SoTransformVec3f()
        self.vec.vector = coin.SbVec3f(0,0,-1)

        # switch with 4 nodes
        self.calc = coin.SoCalculator()
        self.calc.A.connectFrom(self.vec.direction)
        self.calc.expression.set1Value(0, "ta=0.0001") # tolerance
        self.calc.expression.set1Value(1, "tA=vec3f(0,0,1)") # XY plane normal
        self.calc.expression.set1Value(2, "tB=vec3f(0,1,0)") # XZ plane normal
        self.calc.expression.set1Value(3, "tC=vec3f(1,0,0)") # YZ plane normal
        self.calc.expression.set1Value(4, "oa=fabs(dot(A,tA))") # XY value
        self.calc.expression.set1Value(5, "ob=fabs(dot(A,tB))") # XZ value
        self.calc.expression.set1Value(6, "oc=fabs(dot(A,tC))") # YZ value
        self.calc.expression.set1Value(7, "tb=(oa>ob)?oa:ob")
        self.calc.expression.set1Value(8, "tc=(tb>oc)?tb:oc") # winning value
        self.calc.expression.set1Value(9, "tf=(oa==tc)&&((oa+ta)>1)?1:0")
        self.calc.expression.set1Value(10,"tg=(ob==tc)&&((ob+ta)>1)?2:0")
        self.calc.expression.set1Value(11,"th=(oc==tc)&&((oc+ta)>1)?3:0")
        self.calc.expression.set1Value(12,"od=tf+tg+th") # switch value

        # switch with 2 nodes
        self.calc2 = coin.SoCalculator()
        self.calc2.a.connectFrom(self.calc.od)
        self.calc2.expression.set1Value(0, "oa=(a>0)?1:0") # tolerance
        
        self.scaleEngine = coin.SoCalculator()
        #self.scaleEngine.a.connectFrom(cam.height)
        self.scaleEngine.expression.set1Value(0,"ta=floor(log10(a/10))")
        self.scaleEngine.expression.set1Value(1,"tb=pow(10,ta+2)")
        self.scaleEngine.expression.set1Value(2,"oA=vec3f(tb,tb,tb)")
        self.scaleEngine.expression.set1Value(3,"oa=0.01*a/tb")

        self.axis_color = coin.SoCalculator()
        self.axis_color.a.connectFrom(self.calc.od)
        self.axis_color.expression.set1Value(0, "tA=vec3f(0.82, 0.15, 0.15)") # red
        self.axis_color.expression.set1Value(1, "tB=vec3f(0.40, 0.59, 0.20)") # green
        self.axis_color.expression.set1Value(2, "tC=vec3f(0.13, 0.49, 0.88)") # blue
        self.axis_color.expression.set1Value(3, "tD=vec3f(0.00, 0.00, 0.00)") # black
        self.axis_color.expression.set1Value(4, "ta=(a==1)?1:0")
        self.axis_color.expression.set1Value(5, "tb=(a==2)?1:0")
        self.axis_color.expression.set1Value(6, "tc=(a==3)?1:0")
        self.axis_color.expression.set1Value(7, "oA=tD+tB*ta+tC*tb+tB*tc")
        self.axis_color.expression.set1Value(8, "oB=tD+tA*ta+tA*tb+tC*tc")

        self.view_0 = gridView("Not_Ortho")
        self.addChild(self.view_0)
        self.view_1 = gridView("Ortho")
        self.view_1.build_points()
        self.view_1.build_axis()
        self.view_1.build_lines()
        self.addChild(self.view_1)
        
        if cam:
            self.connectCamera(cam)
        else:
            self.whichChild = 0

    def connectCamera(self, cam):
        self.vec.matrix.connectFrom(cam.orientation)
        self.whichChild.connectFrom(self.calc2.oa)
        self.scaleEngine.a.connectFrom(cam.height)
        self.view_1.transform.scaleFactor.connectFrom(self.scaleEngine.oA)
        self.view_1.mat1.diffuseColor.connectFrom(self.axis_color.oA)
        self.view_1.mat2.diffuseColor.connectFrom(self.axis_color.oB)
    def disconnect(self):
        self.whichChild = 0


class orthoViewSwitch(coin.SoSwitch):
    def __init__(self, name = "OrthoViewSwitch", cam = None):
        super(orthoViewSwitch, self).__init__()

        self.setName(name)

        self.vec = coin.SoTransformVec3f()
        self.vec.vector = coin.SbVec3f(0,0,-1)

        self.calc = coin.SoCalculator()
        self.calc.A.connectFrom(self.vec.direction)
        self.calc.expression.set1Value(0, "ta=0.00001") # tolerance
        self.calc.expression.set1Value(1, "tA=vec3f(0,0,1)") # XY plane normal
        self.calc.expression.set1Value(2, "tB=vec3f(0,1,0)") # XZ plane normal
        self.calc.expression.set1Value(3, "tC=vec3f(1,0,0)") # YZ plane normal
        self.calc.expression.set1Value(4, "oa=fabs(dot(A,tA))") # XY value
        self.calc.expression.set1Value(5, "ob=fabs(dot(A,tB))") # XZ value
        self.calc.expression.set1Value(6, "oc=fabs(dot(A,tC))") # YZ value
        self.calc.expression.set1Value(7, "tb=(oa>ob)?oa:ob")
        self.calc.expression.set1Value(8, "tc=(tb>oc)?tb:oc") # winning value
        self.calc.expression.set1Value(9, "tf=(oa==tc)&&((oa+ta)>1)?1:0")
        self.calc.expression.set1Value(10,"tg=(ob==tc)&&((ob+ta)>1)?2:0")
        self.calc.expression.set1Value(11,"th=(oc==tc)&&((oc+ta)>1)?3:0")
        self.calc.expression.set1Value(12,"od=tf+tg+th") # switch value

        self.view_0 = gridView("not_ortho_view")
        self.addChild(self.view_0)
        self.view_z = gridView("Z_view")
        self.addChild(self.view_z)
        self.view_y = gridView("Y_view")
        self.addChild(self.view_y)
        self.view_x = gridView("X_view")
        self.addChild(self.view_x)
        
        if cam:
            self.connectCamera(cam)
        else:
            self.whichChild = 0

    def connectCamera(self, cam):
        self.vec.matrix.connectFrom(cam.orientation)
        self.whichChild.connectFrom(self.calc.od)
    def disconnect(self):
        self.whichChild = 0
    def setTolerance(self, tol):
        self.calc.expression.set1Value(0,"ta=%f"%tol)




trans = coin.SoTranslation()
trans.translation = (2.0,0,0)

color = coin.SoBaseColor()
color.rgb = (0,0,0)

cube = coin.SoCube()

# One text node in each child of the Switch

no = coin.SoText2()
no.string = "View is not orthogonal to any plane"

xy = coin.SoText2()
xy.string = "View is orthogonal to a plane"


# --------------

orthoSwitch = orthoToggleSwitch("Grid")

orthoSwitch.view_0.addChild(no)
orthoSwitch.view_1.addChild(xy)


import FreeCADGui
sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()


#sg.addChild(cube)
sg.addChild(color)
sg.addChild(trans)
sg.addChild(orthoSwitch)


cam = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
# Connect the switch to the camera
orthoSwitch.connectCamera(cam)
# adjust the detection tolerance
#orthoSwitch.setTolerance(0.0001)



#grid = gridView("grid")
#sg.addChild(grid)
#grid.build_points()


