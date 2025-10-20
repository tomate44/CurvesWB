# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCADGui

class selFilter:
    """ Filters FreeCAD selection """
    def __init__(self, sel=[]):
        if sel:
            self.sel = sel
        else:
            self.sel = []
    def setSel(self, sel):
        if sel:
            self.sel = sel
        else:
            self.sel = []
    def getShapes(self, name):
        outlist = []
        shapes = []
        for so in self.sel:
            if so.HasSubObjects:
                for sso,ssoname in zip(so.SubObjects,so.SubElementNames):
                    if name in ssoname:
                        outlist.append((so.Object,ssoname))
                        shapes.append(sso)
        return(outlist,shapes)
    
    def getVertexes(self):
        return(self.getShapes('Vertex'))
    def getEdges(self):
        return(self.getShapes('Edge'))
    def getFaces(self):
        return(self.getShapes('Face'))
    
    def getVertexShapes(self):
        return(self.getVertexes()[1])
    def getEdgeShapes(self):
        return(self.getEdges()[1])
    def getFaceShapes(self):
        return(self.getFaces()[1])
    
    def getVertexLinks(self):
        return(self.getVertexes()[0])
    def getEdgeLinks(self):
        return(self.getEdges()[0])
    def getFaceLinks(self):
        return(self.getFaces()[0])

    def hideAll(self):
        for so in self.sel:
            if hasattr(so.Object,'ViewObject'):
                so.Object.ViewObject.Visibility = False

                
