import FreeCADGui

doc = ''
obj = ''
sob = ''

doc_num = 0
obj_num = 0
face_num = 0
edge_num = 0
vert_num = 0

selection = FreeCADGui.Selection.getSelectionEx()
if selection == []:
    FreeCAD.Console.PrintError('Selection is empty.\n')

for selobj in selection:
    if not selobj.DocumentName == doc:
        doc = selobj.DocumentName
        doc_num += 1
        FreeCADGui.doCommand("doc%d = FreeCAD.getDocument('%s')"%(doc_num,doc))
    if not selobj.ObjectName == obj:
        obj = selobj.ObjectName
        obj_num += 1
        FreeCADGui.doCommand("obj%d = doc%d.getObject('%s')"%(obj_num,doc_num,obj))
    if selobj.HasSubObjects:
        for sub in selobj.SubElementNames:
            if 'Vertex' in sub:
                vert_num += 1
                FreeCADGui.doCommand("vert%d = obj%d.Shape.%s"%(vert_num,obj_num,sub))
            if 'Edge' in sub:
                edge_num += 1
                FreeCADGui.doCommand("edge%d = obj%d.Shape.%s"%(edge_num,obj_num,sub))
            if 'Face' in sub:
                face_num += 1
                FreeCADGui.doCommand("face%d = obj%d.Shape.%s"%(face_num,obj_num,sub))

