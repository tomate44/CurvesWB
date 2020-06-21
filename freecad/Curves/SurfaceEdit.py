import sys
if sys.version_info.major >= 3:
    from importlib import reload
import FreeCAD
import os, time, dummy, FreeCADGui
import Part
from PySide import QtGui, QtCore
from pivy import coin
import loooMarkers as loooMarkers
reload(loooMarkers)

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')


def to1D(pts,weights):
    array = []
    for row,wrow in zip(pts,weights):
        for pt,w in zip(row,wrow):
            array.append((pt.x * w, pt.y * w, pt.z * w, w))
    return array

def toRat4D(pts,weights):
    array = []
    for row,wrow in zip(pts,weights):
        r = []
        for pt,w in zip(row,wrow):
            r.append((pt.x * w, pt.y * w, pt.z * w, w))
        array.append(r)
    return array

def getKnotsMults(array):
    knots = []
    mults = []
    for val in array:
        if val in knots:
            mults[-1] += 1
        else:
            knots.append(val)
            mults.append(1)
    return (knots,mults)

def makeBezierSurface(bs,poles):
    #bs=Part.BezierSurface()
    uLen = len(poles)
    vLen = len(poles[0])
    bs.increase(uLen-1,vLen-1)
    i=0
    for ii in range(uLen):
        for jj in range(vLen):
                bs.setPole(ii+1,jj+1,poles[ii][jj]);
    return(bs)

def makeBSplineSurface(bs,poles):
    #bs=Part.BezierSurface()
    uLen = len(poles)
    vLen = len(poles[0])
    bs.increaseDegree(uLen-1,vLen-1)
    i=0
    for ii in range(uLen):
        for jj in range(vLen):
                bs.setPole(ii+1,jj+1,poles[ii][jj]);
    return(bs)

class coinSurface():
    def __init__(self, surf):
        # The control points for this surface
        self.pts = to1D(surf.getPoles(),surf.getWeights())
        # The knot vector
        try:
            self.Uknots = surf.UKnotSequence
        except:
            self.Uknots = [0.0]*len(surf.getPoles()) + [1.0]*len(surf.getPoles())
        print(str(self.Uknots))
        try:
            self.Vknots = surf.VKnotSequence
        except:
            self.Vknots = [0.0]*len(surf.getPoles()[0]) + [1.0]*len(surf.getPoles()[0])
        print(str(self.Vknots))
        #self.Vknots = surf.VKnotSequence
        self.surfaceNode = coin.SoSeparator()
        self.surfSep = coin.SoSeparator()
       
        # Define the Bezier surface including the control
        # points and a complexity.
        self.material = coin.SoMaterial()
        self.material.transparency.setValue(0.0)
        FreeCAD.Console.PrintMessage("transparency OK\n")
        self.complexity = coin.SoComplexity()
        #self.controlPts = coin.SoCoordinate3()
        self.surface    = coin.SoNurbsSurface()
        self.complexity.value = 1.0
        #self.complexity.type  = self.complexity.SCREEN_SPACE
        self.material.ambientColor.setValue(coin.SbColor(0.3,0,0))
        #self.material.diffuseColor.setValue(coin.SbColor(0.8,1,0.8))
        self.material.specularColor.setValue(coin.SbColor(1,1,1))
        self.material.shininess.setValue(0.5)
        #self.material.transparency.setValue(0.5)
        #self.material.orderedRGBA = 0xcccccc88
        #self.controlPts.point.setValues(0, len(self.pts), self.pts)
        self.surface.numUControlPoints = len(surf.getPoles())
        self.surface.numVControlPoints = len(surf.getPoles()[0])
        self.surface.uKnotVector.setValues(0, len(self.Uknots), self.Uknots)
        self.surface.vKnotVector.setValues(0, len(self.Vknots), self.Vknots)
        self.surfSep.addChild(self.material)
        self.surfSep.addChild(self.complexity)
        #self.surfSep.addChild(self.controlPts)
        self.surfSep.addChild(self.surface)
        self.surfaceNode.addChild(self.surfSep)
        #self.material.transparency.setValue(0.5)
    def update(self,pts):
        #FreeCAD.Console.PrintMessage("coinSurf update\n")
        #self.pts = pts
        #self.controlPts.point.setValues(0,len(self.pts),self.pts)
        #self.material.transparency.setValue(0.5)
        pass

class coinGrid():
    def __init__(self, mlist):
        self.colorRed = coin.SoBaseColor()
        self.colorRed.rgb=(1,0,0)
        self.colorGreen = coin.SoBaseColor()
        self.colorGreen.rgb=(0,1,0)
        self.colorBlue = coin.SoBaseColor()
        self.colorBlue.rgb=(0,0,1)
        self.colorYellow = coin.SoBaseColor()
        self.colorYellow.rgb=(1,1,0)
        self.colorPurple = coin.SoBaseColor()
        self.colorPurple.rgb=(1,0,1)
        self.colorCyan = coin.SoBaseColor()
        self.colorCyan.rgb=(0,1,1)
        self.colorWhite = coin.SoBaseColor()
        self.colorWhite.rgb=(1,1,1)
        self.colorBlack = coin.SoBaseColor()
        self.colorBlack.rgb=(0,0,0)
        self.Ulen = len(mlist)
        self.Vlen = len(mlist[0])
        self.pts = []
        for row in mlist:
            for pt in row:
                self.pts.append(pt.points[0])
        num = []
        for u in range(self.Ulen):
            for v in range(self.Vlen):
                num.append(u*self.Vlen+v)
            num.append(-1)
        num2 = []
        for v in range(self.Vlen):
            for u in range(self.Ulen):
                num2.append(u*self.Vlen+v)
            num2.append(-1)
        print(str(num))
        print(str(num2))
        self.gridSep = coin.SoSeparator()
        #self.coords = coin.SoCoordinate3()
        #self.coords.point.setValues(0,len(self.pts),self.pts)

        self.Line = coin.SoIndexedLineSet()
        self.Line.coordIndex.setValues(0,len(num),num)
        self.Node = coin.SoSeparator()
        #self.Node.addChild(self.coords)
        self.Node.addChild(self.colorBlue)
        self.Node.addChild(self.Line)

        self.Line2 = coin.SoIndexedLineSet()
        self.Line2.coordIndex.setValues(0,len(num2),num2)
        self.Node2 = coin.SoSeparator()
        #self.Node2.addChild(self.coords)
        self.Node2.addChild(self.colorPurple)
        self.Node2.addChild(self.Line2)
        
        self.gridSep.addChild(self.Node)
        self.gridSep.addChild(self.Node2)

    def update(self,pts):
        #FreeCAD.Console.PrintMessage("coinGrid update\n")
        #self.pts = pts
        #self.coords.point.setValues(0,len(self.pts),self.pts)
        pass


class SurfaceEdit(QtGui.QWidget):
    
    def __init__(self):
        super(SurfaceEdit, self).__init__()
        FreeCADGui.Selection.addObserver(self)
        self.grid = None
        self.CoinSurf = None
        self.selectedObject = None
        self.selectedSurface = None
        self.points = None
        self.SoCoords = coin.SoCoordinate4()
        self.cpc = None
        self.viewer = None
        self.render = None
        self.action = None
        self.glAction = None
        self.markerList = []
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.sg = self.view.getSceneGraph()
        self.initUI()
    
    def addSelection(self,doc,obj,sub,pnt):               # Selection object
    #def setPreselection(self,doc,obj,sub):                # Preselection object
        FreeCAD.Console.PrintMessage("addSelection"+ "\n")
        FreeCAD.Console.PrintMessage(str(doc)+ " / ")          # Name of the document
        FreeCAD.Console.PrintMessage(str(obj)+ " / ")          # Name of the object
        FreeCAD.Console.PrintMessage(str(sub)+ " / ")          # The part of the object name
        FreeCAD.Console.PrintMessage(str(pnt)+ "\n")          # Coordinates of the object
        FreeCAD.Console.PrintMessage("______"+ "\n")
        self.apply()
        self.clear()
        self.getSelection()

    def removeSelection(self,doc,obj,sub):                # Delete the selected object
        FreeCAD.Console.PrintMessage("removeSelection"+ "\n")
    def setSelection(self,doc):                           # Selection in ComboView
        FreeCAD.Console.PrintMessage("setSelection"+ "\n")
    def clearSelection(self,doc):                         # If click on the screen, clear the selection
        FreeCAD.Console.PrintMessage("clearSelection"+ "\n")  # If click on another object, clear the previous object
        #self.clear()

    def updateViewObjects(self):
        #FreeCAD.Console.PrintMessage("updateViewObjects started"+ "\n")
        pts = []
        for row in self.markerList:
            for pt in row:
                pts.append(pt.points[0])
        self.Points = pts
        self.SoCoords.point.setValues(0,0,[])
        self.SoCoords.point.setValues(0,len(self.Points),self.Points)
        #self.CoinSurf.update(pts)
        #self.grid.update(pts)
        #self.CoinSurf.material.transparency.setValue(0.0)

    def buildViz(self):
        self.viewer=self.view.getViewer()
        FreeCAD.Console.PrintMessage(str(self.viewer)+ "\n")
        self.render=self.viewer.getSoRenderManager()
        FreeCAD.Console.PrintMessage(str(self.render)+ "\n")
        self.render.setRenderMode(self.render.WIREFRAME_OVERLAY)
        self.action=self.render.getGLRenderAction()
        FreeCAD.Console.PrintMessage(str(self.action.getTypeId().getName())+ "\n") # => "SoBoxSelectionRenderAction" is our own class
        
        if ( str(self.action.getTypeId().getName()) == "SoBoxSelectionRenderAction" ): # replace it with the standard render action
            self.glAction=coin.SoGLRenderAction(self.render.getViewportRegion())
            FreeCAD.Console.PrintMessage(str(self.glAction)+ "\n")
            self.render.setGLRenderAction(self.glAction)
            FreeCAD.Console.PrintMessage('setGLRenderAction : OK'+ "\n")
        self.cpc = loooMarkers.Container()    # control point container
        self.markerList = []
        array = toRat4D(self.selectedSurface.getPoles(), self.selectedSurface.getWeights())
        for j in range(len(array[0])):
            markerRow = []
            for i in range(len(array)):
                p = [array[i][j][0], array[i][j][1], array[i][j][2], array[i][j][3]] #[pt.x, pt.y, pt.z, pt.w]
                marker = loooMarkers.Marker([p], dynamic=True)
                markerRow.append(marker)
            self.markerList.append(markerRow)
        
        self.markerList[0][0].marker.markerIndex = coin.SoMarkerSet.SQUARE_FILLED_9_9
        self.markerList[0][-1].marker.markerIndex = coin.SoMarkerSet.DIAMOND_FILLED_9_9 #SQUARE_FILLED_9_9
        self.markerList[-1][0].marker.markerIndex = coin.SoMarkerSet.TRIANGLE_FILLED_9_9

        for row in self.markerList:
            self.cpc.addChildren(row)
        
        self.cpc.nbUPoles = len(self.markerList)
        self.cpc.nbVPoles = len(self.markerList[0])

        self.updateViewObjects()
        self.CoinSurf = coinSurface(self.selectedSurface)
        self.grid = coinGrid(self.markerList)
        self.vizSep = coin.SoSeparator()
        self.vizSep.addChild(self.SoCoords)
        self.vizSep.addChild(self.grid.gridSep)
        FreeCAD.Console.PrintMessage("Grid added\n")
        self.vizSep.addChild(self.CoinSurf.surfaceNode)
        FreeCAD.Console.PrintMessage("Surface added\n")
        self.vizSep.addChild(self.cpc)
        FreeCAD.Console.PrintMessage("container added\n")
        self.cpc.register(self.view)
        FreeCAD.Console.PrintMessage("container registered\n")
        self.sg.addChild(self.vizSep)
        #self.sg.addChild(self.grid.gridSep)
        #FreeCAD.Console.PrintMessage("Grid added\n")
        #self.sg.addChild(self.CoinSurf.surfaceNode)
        #FreeCAD.Console.PrintMessage("Surface added\n")

        self.cpc.on_drag.append(self.updateViewObjects)
        
    def getSelection(self):
        self.selectedSurface = None
        self.surfaceType = None
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel != []:
            sel0 = sel[0]
            if sel0.HasSubObjects:
                ss = sel0.SubObjects[0]
                if ss.ShapeType == 'Face':
                    surf = ss.Surface
                    self.selectedFace = ss
                    self.selectedObject = sel0.Object
                    if "Wireframe" in self.selectedObject.ViewObject.listDisplayModes():
                        self.selectedObject.ViewObject.DisplayMode = "Wireframe"
                    if issubclass(type(surf),Part.BezierSurface):
                        self.selectedSurface = surf
                        self.surfaceType = "Bezier"
                        FreeCAD.Console.PrintMessage("Bezier Surface Selected\n")
                        self.buildViz()
                        FreeCAD.Console.PrintMessage("buildViz OK\n")
                    elif issubclass(type(surf),Part.BSplineSurface):
                        self.selectedSurface = surf
                        self.surfaceType = "BSpline"
                        FreeCAD.Console.PrintMessage("BSpline Surface Selected\n")
                        self.buildViz()
                        FreeCAD.Console.PrintMessage("buildViz OK\n")
                    else:
                        FreeCAD.Console.PrintMessage(str(surf) + " Selected\n")
                        self.selectedSurface = ss.toNurbs().Faces[0].Surface
                        self.surfaceType = "BSpline"
                        FreeCAD.Console.PrintMessage("Converted to BSpline Surface\n")
                        self.buildViz()
                        FreeCAD.Console.PrintMessage("buildViz OK\n")

    def initUI(self):     
        self.getSelection()

        self.value = 99
        self.sliderRange = 100
       
        self.val = QtGui.QLabel(self)
        self.val.setText('Surface Display')
        self.val.setGeometry(80, 15, 180, 30)
       
        sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld.setFocusPolicy(QtCore.Qt.NoFocus)
        sld.setMaximum(self.sliderRange)
        sld.setGeometry(30, 40, 200, 30)
        sld.setValue(99)
        sld.valueChanged[int].connect(self.changeComplexity)
       
        self.txt = QtGui.QLabel(self)
        self.txt.setText('Fast                                  Fine')
        self.txt.setGeometry(30, 55, 240, 30)

        self.value2 = 0
        self.sliderRange2 = 100
       
        self.val2 = QtGui.QLabel(self)
        self.val2.setText('Surface Transparency')
        self.val2.setGeometry(80, 140, 180, 30)
       
        sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld2.setFocusPolicy(QtCore.Qt.NoFocus)
        sld2.setMaximum(self.sliderRange2)
        sld2.setGeometry(30, 160, 200, 30)
        sld2.valueChanged[int].connect(self.changeTransparency)
       
        self.txt2 = QtGui.QLabel(self)
        self.txt2.setText('0                                  100')
        self.txt2.setGeometry(30, 175, 240, 30)

        self.OKButton = QtGui.QPushButton("OK",self)
        self.OKButton.clicked.connect(self.activate)
        self.OKButton.setAutoDefault(False)
        self.OKButton.move(30, 260)
       
        self.cancelButton = QtGui.QPushButton('Quit', self)
        self.cancelButton.clicked.connect(self.onCancel)
        self.cancelButton.setAutoDefault(True)
        self.cancelButton.move(130, 260)
        FreeCAD.Console.PrintMessage("InitUI OK\n")

        self.doc1 = QtGui.QLabel(self)
        self.doc1.setText('\'g\' : Grab selected poles')
        self.doc1.setGeometry(30, 340, 180, 30)

        self.doc2 = QtGui.QLabel(self)
        self.doc2.setText('\'x\',\'y\',\'z\' : Axis constraint')
        self.doc2.setGeometry(30, 380, 180, 30)

    def rounded(self,v):
        return(str(int(v*100)/100.))
   
    def changeComplexity(self, value):
        FreeCAD.Console.PrintMessage("UI changeValue\n")
        self.value = value
        v = 1. * value / (self.sliderRange)
        if self.CoinSurf:
            self.CoinSurf.complexity.value = v

    def changeTransparency(self, value):
        FreeCAD.Console.PrintMessage("UI changeValue\n")
        self.value2 = value
        v = 1. * value / (self.sliderRange2)
        if self.CoinSurf:
            self.CoinSurf.material.transparency.setValue(v)    

    def apply(self):
        t = time.time()
        if 1: #self.surfaceType == "Bezier":
            #FreeCAD.Console.PrintMessage(str(self.selectedSurface.getPoles()))
            poles = []
            weights = []
            for j in range(len(self.markerList[0])):
                ptrow= []
                wrow = []
                for i in range(len(self.markerList)):
                    w = self.markerList[i][j].points[0][3]
                    if w:
                        v = FreeCAD.Vector(self.markerList[i][j].points[0][0]/w,self.markerList[i][j].points[0][1]/w,self.markerList[i][j].points[0][2]/w)
                    else:
                        v = FreeCAD.Vector(0,0,0)
                    FreeCAD.Console.PrintMessage(str(v)+" - "+str(w)+"\n")
                    ptrow.append(v)
                    wrow.append(w)
                poles.append(ptrow)
                weights.append(wrow)
            #FreeCAD.Console.PrintMessage("Weight - "+str(weights)+"\n")
            if self.surfaceType == "BSpline":
                s = Part.BSplineSurface()
                #s = makeBSplineSurface(s, poles)
                #FreeCAD.Console.PrintMessage("UKnots : " + str(self.CoinSurf.Uknots) + "\n")
                Ukm = getKnotsMults(self.CoinSurf.Uknots)
                Uknots = Ukm[0]
                Umults = Ukm[1]
                Vkm = getKnotsMults(self.CoinSurf.Vknots)
                Vknots = Vkm[0]
                Vmults = Vkm[1]
                Udeg = len(self.CoinSurf.Uknots) - len(poles) - 1
                Vdeg = len(self.CoinSurf.Vknots) - len(poles[0]) - 1
                s.buildFromPolesMultsKnots(poles,Umults,Vmults,Uknots,Vknots,False,False,Udeg,Vdeg,weights)
            #FreeCAD.Console.PrintMessage("Weight - "+str(s.getWeights())+"\n")
            elif self.surfaceType == "Bezier":
                s = Part.BSplineSurface()
                #s = makeBSplineSurface(s, poles)
                #FreeCAD.Console.PrintMessage("UKnots : " + str(self.CoinSurf.Uknots) + "\n")
                Ukm = getKnotsMults(self.CoinSurf.Uknots)
                Uknots = Ukm[0]
                Umults = Ukm[1]
                Vkm = getKnotsMults(self.CoinSurf.Vknots)
                Vknots = Vkm[0]
                Vmults = Vkm[1]
                Udeg = len(self.CoinSurf.Uknots) - len(poles) - 1
                Vdeg = len(self.CoinSurf.Vknots) - len(poles[0]) - 1
                s.buildFromPolesMultsKnots(poles,Umults,Vmults,Uknots,Vknots,False,False,Udeg,Vdeg,weights)
                
                #************   Crash with oce 0.17  *******************
                #s = Part.BezierSurface()
                #uLen = len(poles)
                #vLen = len(poles[0])
                #s.increase(uLen-1,vLen-1)
                #for ii in range(uLen):
                    #for jj in range(vLen):
                            #s.setPole(  ii+1,jj+1,poles[ii][jj])
                            #s.setWeight(ii+1,jj+1,weights[ii][jj])
                ##for i in range(len(weights)):
                    ##for j in range(len(weights[i])):
                        ##FreeCAD.Console.PrintMessage("Weight - "+str(i+1)+ "  "+str(j+1)+ " -> " + str(weights[i][j]) + "\n")
                        ##s.setWeight(i+1,j+1,weights[i][j])
            faces = []
            for f in self.selectedObject.Shape.Faces:
                if not f.isSame(self.selectedFace):
                    print(str(f))
                    faces.append(f)
            faces.append(s.toShape())
            print(str(faces))
            shell = Part.Shell(faces)
            Part.show(shell)
            #self.selectedObject.ViewObject.Visibility = False
        FreeCAD.Console.PrintMessage(str(time.time()-t))

    def activate(self):
        self.apply()   
        self.onCancel()
        if "Wireframe" in self.selectedObject.ViewObject.listDisplayModes():
            self.selectedObject.ViewObject.DisplayMode = "Wireframe"

    def clear(self):
        if self.selectedObject:
            if "Flat Lines" in self.selectedObject.ViewObject.listDisplayModes():
                self.selectedObject.ViewObject.DisplayMode = "Flat Lines"
            self.selectedObject.touch()
            if self.render:
                self.render.setRenderMode(self.render.AS_IS)
            #if self.CoinSurf:
                #self.sg.removeChild(self.CoinSurf.surfaceNode)
            #if self.grid:
                #self.sg.removeChild(self.grid.gridSep)
            #if self.SoCoords:
                #self.sg.removeChild(self.SoCoords)
            if self.cpc:
                self.cpc.removeAllChildren()
                self.cpc.unregister()
            if self.vizSep:
                self.sg.removeChild(self.vizSep)
            FreeCAD.activeDocument().recompute()

    def onCancel(self):
        self.clear()
        FreeCADGui.Selection.removeObserver(self)                   # Uninstall the resident function
        mw = getMainWindow()
        tab = getComboView(getMainWindow())
        tab.removeTab(2)
        SurfaceEditTool.active = False
        



def getMainWindow():
   "returns the main window"
   # using QtGui.qApp.activeWindow() isn't very reliable because if another
   # widget than the mainwindow is active (e.g. a dialog) the wrong widget is
   # returned
   toplevel = QtGui.qApp.topLevelWidgets()
   for i in toplevel:
       if i.metaObject().className() == "Gui::MainWindow":
           return i
   raise Exception("No main window found")

def getComboView(mw):
   dw=mw.findChildren(QtGui.QDockWidget)
   for i in dw:
       if str(i.objectName()) == "Combo View":
           return i.findChild(QtGui.QTabWidget)
       elif str(i.objectName()) == "Python Console":
           return i.findChild(QtGui.QTabWidget)
   raise Exception ("No tab widget found")

class SurfaceEditTool:
    def __init__(self):
        SurfaceEditTool.active = False
    def Activated(self):
        if not SurfaceEditTool.active:
            mw = getMainWindow()
            tab = getComboView(getMainWindow())

            tab2=SurfaceEdit()
            tab.addTab(tab2,"Surface Edit Tool")
            tab2.show()   #zebraWidget.show()   
            SurfaceEditTool.active = True
        else:
            FreeCAD.Console.PrintMessage("Tool already active\n")

    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/surfEdit.svg', 'MenuText': 'SurfaceEditTool', 'ToolTip': 'Edit NURBS Surfaces'}

FreeCADGui.addCommand('SurfaceEditTool', SurfaceEditTool())
