import sys
import os
import FreeCADGui
from pivy import coin
import _utils

filepath = os.path.dirname(_utils.__file__)

#from PySide2 import QtGui
#from pivy import coin, quarter
#from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton


def insert():
    
    vert = coin.SoVertexShader()
    vert.sourceProgram = os.path.join(filepath,"shader_vertex.glsl")
    
    frag = coin.SoFragmentShader()
    frag.sourceProgram = os.path.join(filepath,"shader_fragment.glsl")
    
    shaders = [vert,frag]
    pro = coin.SoShaderProgram()
    pro.shaderObject.setValues(0,len(shaders),shaders)
    
    sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
    sg.insertChild(pro,1)
    
def remove(idx=1):
    sg = FreeCADGui.ActiveDocument.ActiveView.getSceneGraph()
    sg.removeChild(1)

