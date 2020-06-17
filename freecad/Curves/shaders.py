import sys

from PySide2 import QtGui
from pivy import coin, quarter
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton

import FreeCADGui as Gui

import os
import _utils
path = os.path.dirname(_utils.__file__)

def insert():
    sg = Gui.ActiveDocument.ActiveView.getSceneGraph()
    shaders = list()
    
    vert = coin.SoVertexShader()
    vert.sourceProgram = os.path.join(path,"shaders_vertex.glsl")
    shaders.append(vert)
    
    frag = coin.SoFragmentShader()
    frag.sourceProgram = os.path.join(path,"shaders_fragment.glsl")
    shaders.append(frag)
    
    pro = coin.SoShaderProgram()
    pro.shaderObject.setValues(0,len(shaders),shaders)
    
    sg.insertChild(pro,0)
    return pro

def remove():
    sg = Gui.ActiveDocument.ActiveView.getSceneGraph()
    sg.removeChild(0)

def main():
    app = QApplication(sys.argv)

    root = coin.SoSeparator()
    

    vert = coin.SoVertexShader()
    vert.sourceProgram = "vertex.glsl"
    
    frag = coin.SoFragmentShader()
    frag.sourceProgram = "frag.glsl"
    
    shaders = [vert,frag]
    pro = coin.SoShaderProgram()
    pro.shaderObject.setValues(0,len(shaders),shaders)
    
    
    mat = coin.SoMaterial()
    mat.diffuseColor.setValue(coin.SbColor(0.8, 0.8, 0.8))
    mat.specularColor.setValue(coin.SbColor(1, 1, 1))
    mat.shininess.setValue(1.0)
    mat.transparency.setValue(0.5)
    
    
    
    
    sphere = coin.SoSphere()
    sphere.radius = 1.2
    
    
    root.addChild(pro)
    root.addChild(sphere)
    root.addChild(mat)
    root.addChild(coin.SoCube())

    viewer = quarter.QuarterWidget()
    viewer.setSceneGraph(root)

    viewer.setWindowTitle("minimal")
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

