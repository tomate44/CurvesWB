# -*- coding: utf-8 -*-

__title__ = "Selection Processor"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = """Filter and process FreeCADGui Selection"""

import FreeCAD
import FreeCADGui
import Part


class SelectionProcessor:
    """Filter and process FreeCADGui Selection"""
    def __init__(self, sel=None):
        self.selection = sel
        self.links = None
    
