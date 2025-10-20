# SPDX-License-Identifier: LGPL-2.1-or-later

__title__ = "import3DM"
__author__ = "Christophe Grellier (Chris_G) - Keith Sloan (keithsloan52)"
__license__ = "LGPL 2.1"
__doc__ = "import of 3DM file"

import FreeCAD
import os, io, sys
import FreeCADGui
import Part

if open.__module__ == '__builtin__':
    pythonopen = open # to distinguish python built-in open function from the one declared here

def open(filename):
    "called when freecad opens a file."
    global doc
    docname = os.path.splitext(os.path.basename(filename))[0]
    doc = FreeCAD.newDocument(docname)
    if filename.lower().endswith('.3dm'):
        process3DM(doc,filename)
    return doc

def insert(filename,docname):
    "called when freecad imports a file"
    global doc
    groupname = os.path.splitext(os.path.basename(filename))[0]
    try:
        doc=FreeCAD.getDocument(docname)
    except NameError:
        doc=FreeCAD.newDocument(docname)
    if filename.lower().endswith('.3dm'):
        process3DM(doc,filename)

def process3DM(doc, filename) :
    FreeCAD.Console.PrintMessage('Import 3DM file : '+filename+'\n')
    FreeCAD.Console.PrintMessage('Import3DM Version 0.1\n')

    pathName = os.path.dirname(os.path.normpath(filename))
    print("Add code to parse 3DM file")

    FreeCAD.Console.PrintMessage('3DM File Imported\n')


    

