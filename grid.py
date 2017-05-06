from pivy import coin

class gridNode(coin.SoSeparator):
    def __init__(self):
        super(gridNode, self).__init__()

        self.gridColor = coin.SoMaterial()
        self.line1Color = coin.SoMaterial()
        self.line2Color = coin.SoMaterial()
        self.gridCoord = coin.SoCoordinate3()
        self.line1Coord = coin.SoCoordinate3()
        self.line2Coord = coin.SoCoordinate3()
        self.line1 = coin.SoLineSet()
        self.line2 = coin.SoLineSet()
        self.grid = coin.SoIndexedLineSet()

        self.addChild(self.line1Color)
        self.addChild(self.line1Coord)
        self.addChild(self.line1)
        self.addChild(self.line2Color)
        self.addChild(self.line2Coord)
        self.addChild(self.line2)
        self.addChild(self.gridColor)
        self.addChild(self.gridCoord)
        self.addChild(self.grid)

    def setVector1(self, vec=(1,0,0), color=(1,0,0)):
        self.vector1 = coin.SbVector3f(vec)
        self.line1Color.diffuseColor = color

    def setVector2(self, vec=(0,1,0), color=(0,1,0)):
        self.vector2 = coin.SbVector3f(vec)
        self.line2Color.diffuseColor = color

    def setGeom(self, main=100, sub=10):
        self.mainDim = main
        self.subDim = sub

    def buildGrid(self):
        pts = []
        for i in range(sub, main, sub):
            for j in range(sub, main, sub):
                pts.append()