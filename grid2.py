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
        ds.pointSize = 3
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

    #@property
    #def number_of_points(self):
        #return(self._number_of_points)

    #@number_of_points.setter
    #def number_of_points(self, n):
        #self._number_of_points = n
        #if n == 0:
            #self._number_of_points = 50
        #self.coord = coin.SoCoordinate3()
        #self.build_points()

    def build_points(self):
        pts = list()
        sc = 1. / self._number_of_points
        for i in range(-self._number_of_points, self._number_of_points + 1):
            for j in range(-self._number_of_points,self._number_of_points + 1):
                pts.append(coin.SbVec3f(sc * i, sc * j, 0))
        self.coord.point.setValues(0, len(pts), pts)
        

class orthoToggleSwitch(coin.SoSwitch):
    def __init__(self, name = "ToggleSwitch", cam = None):
        super(orthoToggleSwitch, self).__init__()

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

        self.calc2 = coin.SoCalculator()
        self.calc2.a.connectFrom(self.calc.od)
        self.calc2.expression.set1Value(0, "oa=(a>0)?1:0") # tolerance
        
        self.scaleEngine = coin.SoCalculator()
        #self.scaleEngine.a.connectFrom(cam.height)
        self.scaleEngine.expression.set1Value(0,"ta=floor(log10(a/10))")
        self.scaleEngine.expression.set1Value(1,"tb=pow(10,ta+2)")
        self.scaleEngine.expression.set1Value(2,"oA=vec3f(tb,tb,tb)")
        self.scaleEngine.expression.set1Value(3,"oa=0.01*a/tb")

        self.view_0 = gridView("Not_Ortho")
        self.addChild(self.view_0)
        self.view_1 = gridView("Ortho")
        self.view_1.build_points()
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


