# -*- coding: utf-8 -*-

__title__ = "Property Editor"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Property editor for FeaturePython objects."

import FreeCAD
from pivy import coin

class Manager(object):
    def __init__(self, fp):
        self.fp = fp
        self.draggers = list()
        self.root = coin.SoSeparator()
        self.parent = fp.ViewObject.RootNode
        self.parent.addChild(self.root)
    def addDragger(self, dragger):
        self.draggers.append(dragger)
    def showDragger(self, dragger=None):
        if dragger:
            self.root.addChild(dragger.root)
        else:
            for d in self.draggers:
                self.showDragger(d)
    def quit(self):
        self.parent.removeChild(self.root)
    
        

class Dragger(object):
    def __init__(self, manager, prop, drag = None):
        self.manager = manager
        self.prop = prop
        if drag is None:
            self.dragger = self.get_default_dragger()
        else:
            self.dragger = drag
        self.root = coin.SoSeparator()
        self.transform = coin.SoTransform()
        self.root.addChild(self.transform)
        self.root.addChild(self.dragger)
    
    def get_default_dragger(self):
        dragger_dict = {"App::PropertyVector":      coin.SoDragPointDragger,
                        "App::PropertyDistance":    coin.SoScale1Dragger,
                        "App::PropertyFloat":       coin.SoTranslate1Dragger}
        prop_type = self.manager.fp.getTypeIdOfProperty(self.prop)
        return(dragger_dict[prop_type]())

