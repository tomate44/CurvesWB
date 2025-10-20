# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
import Part
from pivy import coin

CROSS_5_5 = 0
PLUS_5_5 = 1
MINUS_5_5 = 2
SLASH_5_5 = 3
BACKSLASH_5_5 = 4
BAR_5_5 = 5
STAR_5_5 = 6
Y_5_5 = 7
LIGHTNING_5_5 = 8
WELL_5_5 = 9
CIRCLE_LINE_5_5 = 10
SQUARE_LINE_5_5 = 11
DIAMOND_LINE_5_5 = 12
TRIANGLE_LINE_5_5 = 13
RHOMBUS_LINE_5_5 = 14
HOURGLASS_LINE_5_5 = 15
SATELLITE_LINE_5_5 = 16
PINE_TREE_LINE_5_5 = 17
CAUTION_LINE_5_5 = 18
SHIP_LINE_5_5 = 19
CIRCLE_FILLED_5_5 = 20
SQUARE_FILLED_5_5 = 21
DIAMOND_FILLED_5_5 = 22
TRIANGLE_FILLED_5_5 = 23
RHOMBUS_FILLED_5_5 = 24
HOURGLASS_FILLED_5_5 = 25
SATELLITE_FILLED_5_5 = 26
PINE_TREE_FILLED_5_5 = 27
CAUTION_FILLED_5_5 = 28
SHIP_FILLED_5_5 = 29
CROSS_7_7 = 30
PLUS_7_7 = 31
MINUS_7_7 = 32
SLASH_7_7 = 33
BACKSLASH_7_7 = 34
BAR_7_7 = 35
STAR_7_7 = 36
Y_7_7 = 37
LIGHTNING_7_7 = 38
WELL_7_7 = 39
CIRCLE_LINE_7_7 = 40
SQUARE_LINE_7_7 = 41
DIAMOND_LINE_7_7 = 42
TRIANGLE_LINE_7_7 = 43
RHOMBUS_LINE_7_7 = 44
HOURGLASS_LINE_7_7 = 45
SATELLITE_LINE_7_7 = 46
PINE_TREE_LINE_7_7 = 47
CAUTION_LINE_7_7 = 48
SHIP_LINE_7_7 = 49
CIRCLE_FILLED_7_7 = 50
SQUARE_FILLED_7_7 = 51
DIAMOND_FILLED_7_7 = 52
TRIANGLE_FILLED_7_7 = 53
RHOMBUS_FILLED_7_7 = 54
HOURGLASS_FILLED_7_7 = 55
SATELLITE_FILLED_7_7 = 56
PINE_TREE_FILLED_7_7 = 57
CAUTION_FILLED_7_7 = 58
SHIP_FILLED_7_7 = 59
CROSS_9_9 = 60
PLUS_9_9 = 61
MINUS_9_9 = 62
SLASH_9_9 = 63
BACKSLASH_9_9 = 64
BAR_9_9 = 65
STAR_9_9 = 66
Y_9_9 = 67
LIGHTNING_9_9 = 68
WELL_9_9 = 69
CIRCLE_LINE_9_9 = 70
SQUARE_LINE_9_9 = 71
DIAMOND_LINE_9_9 = 72
TRIANGLE_LINE_9_9 = 73
RHOMBUS_LINE_9_9 = 74
HOURGLASS_LINE_9_9 = 75
SATELLITE_LINE_9_9 = 76
PINE_TREE_LINE_9_9 = 77
CAUTION_LINE_9_9 = 78
SHIP_LINE_9_9 = 79
CIRCLE_FILLED_9_9 = 80
SQUARE_FILLED_9_9 = 81
DIAMOND_FILLED_9_9 = 82
TRIANGLE_FILLED_9_9 = 83
RHOMBUS_FILLED_9_9 = 84
HOURGLASS_FILLED_9_9 = 85
SATELLITE_FILLED_9_9 = 86
PINE_TREE_FILLED_9_9 = 87
CAUTION_FILLED_9_9 = 88
SHIP_FILLED_9_9 = 89




def beautify(shp):
    if not shp:
        return ""
    else:
        if (shp[0] == "<") and (shp[-1] == ">"):
            t = shp[1:-1]
            return t.split()[0]
        else:
            return shp

def removeDecim(arr):
    r = []
    for fl in arr:
        r.append("%0.2f"%fl)
    return r

def getCoinNode(shape):
    import tempfile
    iv = shape.writeInventor()
    temp = tempfile.NamedTemporaryFile()
    temp.write(shape.writeInventor())
    temp.seek(0)
    inp = coin.SoInput()
    #openFile(str(filename.toLatin1()))
    inp.openFile(temp.name)
    root = coin.SoDB.readAll(inp)
    temp.close()
    return(root)


class colorNode(coin.SoSeparator):
    def __init__(self, color = (0.,0.,0.)):
        super(colorNode, self).__init__()
        self.coinColor = coin.SoMaterial()
        self.binding = coin.SoMaterialBinding()
        self.binding.value = coin.SoMaterialBinding.PER_PART
        self.addChild(self.binding)
        self.addChild(self.coinColor)
        self.color = color

    @property
    def color(self):
        ar = [col.getValue() for col in self.coinColor.diffuseColor.getValues()]
        return ar

    @color.setter
    def color(self, color):
        if isinstance(color[0], (tuple, list)):
            #ar = []
            #for col in color:
                #ar.append((col[0], col[1], col[2]))
            self.coinColor.diffuseColor.setValues(0,len(color),color)
        else:
            self.coinColor.diffuseColor.setValues(0,1,[color])

    @property
    def transparency(self):
        return self.coinColor.transparency.getValues()[0].getValue()

    @transparency.setter
    def transparency(self, tr):
        self.coinColor.transparency = tr

class styleNode(colorNode):
    def __init__(self, color = (0.,0.,0.), lineWidth = 1.0, pointSize = 1.0):
        super(styleNode, self).__init__()
        self.drawStyle = coin.SoDrawStyle()
        self.addChild(self.drawStyle)
        self.color = color
        self.lineWidth = lineWidth
        self.pointSize = pointSize

    @property
    def pointSize(self):
        return self.drawStyle.pointSize.getValue()

    @pointSize.setter
    def pointSize(self, pointSize):
        self.drawStyle.pointSize = pointSize

    @property
    def lineWidth(self):
        return self.drawStyle.lineWidth.getValue()

    @lineWidth.setter
    def lineWidth(self, lineWidth):
        self.drawStyle.lineWidth = lineWidth

class polygonNode(styleNode):
    def __init__(self, color = (0.,0.,0.), lineWidth = 1.0):
        super(polygonNode, self).__init__()
        self.lines = coin.SoIndexedLineSet()
        self.addChild(self.lines)
        self.color = color
        self.lineWidth = lineWidth
        self._numVertices = []

    @property
    def vertices(self):
        return self._numVertices

    @vertices.setter
    def vertices(self, arr):
        if len(arr) == 0:
            self.lines.coordIndex.setValue(0)
            self._numVertices = 0
            col = self.color[0]
            self.color = [col]
        else:
            a = list(range(len(arr)))
            a.append(-1)
            self.lines.coordIndex.setValue(0)
            self.lines.coordIndex.setValues(0, len(a), a)
            self._numVertices = a
            col = self.color[0]
            self.color = [col]*len(a)

    def setFirstColor(self, col):
        collist = self.color
        collist[0] = col
        self.color = collist
        
    def setLastColor(self, col):
        collist = self.color
        collist[-1] = col
        self.color = collist

class rowNode(polygonNode):
    def __init__(self, color = (0.,0.,0.), lineWidth = 1.0):
        super(rowNode, self).__init__(color, lineWidth)

    @polygonNode.vertices.setter
    def vertices(self, uv):
        a = []
        for u in range(uv[0]):
            for v in range(uv[1]):
                a.append(uv[1] * u + v)
            a.append(-1)
        self.lines.coordIndex.setValue(0)
        self.lines.coordIndex.setValues(0, len(a), a)
        self._numVertices = a

class colNode(polygonNode):
    def __init__(self, color = (0.,0.,0.), lineWidth = 1.0):
        super(colNode, self).__init__(color, lineWidth)

    @polygonNode.vertices.setter
    def vertices(self, uv):
        a = []
        for v in range(uv[1]):
            for u in range(uv[0]):
                a.append(uv[1] * u + v)
            a.append(-1)
        self.lines.coordIndex.setValue(0)
        self.lines.coordIndex.setValues(0, len(a), a)
        self._numVertices = a

class sensorPolyNode(styleNode):
    def __init__(self, color = (0.,0.,0.), lineWidth = 1.0):
        super(sensorPolyNode, self).__init__()
        self.lines = coin.SoIndexedLineSet()
        self.addChild(self.lines)
        self.color = color
        self.lineWidth = lineWidth

    def linkTo(self, node):
        self.sensor = coin.SoFieldSensor(self.updateCB, node)
        #self.sensor.setFunction(self.updateCB)
        #self.Sensor.setData(node)
        self.sensor.setPriority(0)
        self.sensor.attach(node.point)
        
    def unlink(self):
        self.sensor.detach()

    def updateCB(self, *args):
        points = self.sensor.getTriggerField()
        l = len(points)
        a = list(range(l))
        a.append(-1)
        self.lines.coordIndex.setValue(0)
        self.lines.coordIndex.setValues(0, len(a), a)

class combComb(sensorPolyNode):
    def __init__(self, color = (0.,0.7,0.), lineWidth = 1.0):
        super(combComb, self).__init__(color, lineWidth)

    def updateCB(self, *args):
        points = self.sensor.getTriggerField()
        #points = self.sensor.getAttachedField()
        a = []
        l = len(points)
        for i in range(l/2.0):
            a.append(2*i)
            a.append(2*i+1)
            a.append(-1)
        self.lines.coordIndex.setValue(0)
        self.lines.coordIndex.setValues(0, len(a), a)
        #print("combComb : %d"%len(self.lines.coordIndex.getValues()))

class combCurve(sensorPolyNode):
    def __init__(self, color = (0.7,0.,0.), lineWidth = 1.0):
        super(combCurve, self).__init__(color, lineWidth)

    def updateCB(self, *args):
        points = self.sensor.getTriggerField()
        #points = self.sensor.getAttachedField()
        a = []
        l = len(points)
        for i in range(l/2.0):
            a.append(2*i+1)
        a.append(-1)
        self.lines.coordIndex.setValue(0)
        self.lines.coordIndex.setValues(0, len(a), a)
        #print("combCurve : %d"%len(self.lines.coordIndex.getValues()))

class coordinate3Node(coin.SoCoordinate3):
    def __init__(self, points = []):
        super(coordinate3Node, self).__init__()
        self.points = points

    @property
    def points(self):
        r = []
        for p in self.point.getValues():
            r.append(p.getValue())
        return r

    @points.setter
    def points(self, pts):
        self.point.setValue(0,0,0)
        self.point.setValues(0, len(pts), pts)

    def add(self, pt):
        pts = self.points
        pts.append(pt)
        self.points = pts

    def pop(self, i):
        pts = self.points
        pts.pop(i)
        self.points = pts

class markerSetNode(colorNode):
    def __init__(self, color = (0.,0.,0.), marker = 0):
        super(markerSetNode, self).__init__()
        self.markers = coin.SoMarkerSet()
        self.addChild(self.markers)
        self.color = [color]
        self.marker = marker

    @property
    def marker(self):
        return self.markers.markerIndex.getValues()[0]

    @marker.setter
    def marker(self, marker):
        self.markers.markerIndex = marker

class text2dNode(colorNode):
    def __init__(self, color = (0.,0.,0.), font = 'sans', size = 16, trans = (0,0,0), text = ''):
        super(text2dNode, self).__init__()
        self.fontNode = coin.SoFont()
        self.transNode = coin.SoTransform()
        self.textNode = coin.SoText2()
        self.addChild(self.fontNode)
        self.addChild(self.transNode)
        self.addChild(self.textNode)
        self.color = color
        self.font = font
        self.size = size
        self.trans = trans
        self.text = text

    @property
    def font(self):
        return self.fontNode.name.getValue()

    @font.setter
    def font(self, name):
        self.fontNode.name = name

    @property
    def size(self):
        return self.fontNode.size.getValue()

    @size.setter
    def size(self, size):
        self.fontNode.size.setValue(size)

    @property
    def trans(self):
        return self.transNode.translation.getValue().getValue()

    @trans.setter
    def trans(self, trans):
        self.transNode.translation.setValue([trans[0],trans[1],trans[2]])

    @property
    def text(self):
        return self.textNode.string.getValues()[0]

    @text.setter
    def text(self, text):
        self.textNode.string = text

class multiTextNode(colorNode):
    def __init__(self, color = (0.,0.,0.), font = 'sans', size = 16, offset = 0):
        super(multiTextNode, self).__init__()
        self.fontNode = coin.SoFont()
        self.textSep = coin.SoSeparator()
        self.nodeList = []
        self._data = []
        self.addChild(self.fontNode)
        self.addChild(self.textSep)
        self.color = color
        self.font = font
        self.size = size
        self.offset = offset

    @property
    def font(self):
        return self.fontNode.name.getValue()

    @font.setter
    def font(self, name):
        self.fontNode.name = name

    @property
    def size(self):
        return self.fontNode.size.getValue()

    @size.setter
    def size(self, size):
        self.fontNode.size.setValue(size)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, datarr):
        if not ((len(self._data) == len(datarr[0])) & (len(self._data) == len(datarr[1]))): # lengths of the 2 arrays are different. Wipe the Separator and populate it.
            self.nodeList = []
            self._data = []
            self.textSep.removeAllChildren()
            for i in range(min(len(datarr[0]),len(datarr[1]))):
                sep = coin.SoSeparator()
                textpos = coin.SoTransform()
                textpos.translation.setValue([datarr[0][i][0],datarr[0][i][1],datarr[0][i][2]])
                text = coin.SoText2()
                field = [""]*self.offset + [datarr[1][i]]
                text.string.setValues(0,len(field),field)
                sep.addChild(textpos)
                sep.addChild(text)
                self.textSep.addChild(sep)
                self.nodeList.append((textpos,text))
                self._data.append((datarr[0][i],datarr[1][i]))
        else:
            for i in range(min(len(datarr[0]),len(datarr[1]))):
                print(range(min(len(datarr[0]),len(datarr[1]))))
                print(self.nodeList[i][0])
                self.nodeList[i][0].translation.setValue([datarr[0][i][0],datarr[0][i][1],datarr[0][i][2]])
                field = [""]*self.offset + [datarr[1][i]]
                self.nodeList[i][1].string.setValues(0,len(field),field)
                self._data[i] = (datarr[0][i],datarr[1][i])


#c = coordinate3Node([(0,1,0),(1,1,0),(2,2,1)])
#p = polygonNode((0.5,0.9,0.1),2)
#m = markerSetNode((1,0.35,0.8),1)
#t = text2dNode((0.2,0.9,0.9),'osiFont',15,(10,15,20),'blabla')
#mt = multiTextNode((0.2,0.9,0.9),'osiFont',15,(10,15,20))
#mt.data = ([(1,2,3),(4,5,6)],['bla','blublu'])


