# -*- coding: utf-8 -*-

__title__ = "Curves workbench utilities"
__author__ = "Christophe Grellier (Chris_G)"
__license__ = "LGPL 2.1"
__doc__ = "Curves workbench utilities common to all tools."

import FreeCAD

def setIconsPath(path):
    global icons_path
    icons_path = path
    return True

def iconsPath():
    global icons_path
    return icons_path

def info(string):
    FreeCAD.Console.PrintMessage("%s\n"%string)
    
def warn(string):
    FreeCAD.Console.PrintWarning("%s\n"%string)

def error(string):
    FreeCAD.Console.PrintError("%s\n"%string)

def debug(string):
    FreeCAD.Console.PrintMessage("%s\n"%string)

def doNothing(string):
    return None

def setEditorMode(fp, group, mode):
    """set the editor mode of a group of properties"""
    for prop in group:
        fp.setEditorMode(prop, mode)

def getSubShape(shape, shape_type, n):
    if shape_type == "Vertex" and len(shape.Vertexes) >= n:
        return shape.Vertexes[n-1]
    elif shape_type == "Edge" and len(shape.Edges) >= n:
        return shape.Edges[n-1]
    elif shape_type == "Face" and len(shape.Faces) >= n:
        return shape.Faces[n-1]
    else:
        return None

def getShape(obj, prop, shape_type):
    if hasattr(obj, prop) and obj.getPropertyByName(prop):
        if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSub":
            n = eval(obj.getPropertyByName(prop)[1][0].lstrip(shape_type))
            sh = obj.getPropertyByName(prop)[0].Shape.copy()
            if sh and hasattr(obj.getPropertyByName(prop)[0], "getGlobalPlacement"):
                pl = obj.getPropertyByName(prop)[0].getGlobalPlacement()
                sh.Placement = pl
            return getSubShape(sh, shape_type, n)
        elif obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
            res = []
            for tup in obj.getPropertyByName(prop):
                for ss in tup[1]:
                    n = eval(ss.lstrip(shape_type))
                    sh = tup[0].Shape.copy()
                    if sh and hasattr(tup[0], "getGlobalPlacement"):
                        pl = tup[0].getGlobalPlacement()
                        sh.Placement = pl
                    res.append(getSubShape(sh, shape_type, n))
            return res
        else:
            FreeCAD.Console.PrintError("CurvesWB._utils.getShape: wrong property type.\n")
            return None
    else:
        FreeCAD.Console.PrintError("CurvesWB._utils.getShape: %r has no property %r\n"%(obj, prop))
        return None

def same_direction(e1, e2, num=10):
    """bool = same_direction(e1, e2, num=10)
    Check if the 2 entities have same direction,
    by comparing them on 'num' samples.
    Entities can be : edges, wires or curves
    """
    v1 = []
    v2 = []
    pts1 = e1.discretize(num)
    pts2 = e2.discretize(num)
    for i in range(num):
        v1.append(pts1[i].distanceToPoint(pts2[i]))
        v2.append(pts1[i].distanceToPoint(pts2[num-1-i]))
    if sum(v1) < sum(v2):
        return True
    else:
        return False

def info_subshapes(shape):
    """Print the list of subshapes of a shape in FreeCAD console.
    info_subshapes(my_shape)
    """
    sh = ["Solids",
          "Compounds",
          "CompSolids",
          "Shells",
          "Faces",
          "Wires",
          "Edges",
          "Vertexes"]
    info("-> Content of {}".format(shape.ShapeType))
    for s in sh:
        subs = shape.__getattribute__(s)
        if subs:
            if (len(subs) == 1) and (subs[0].isEqual(shape)):
                pass # hide self
            else:
                info("{}: {}".format(s, len(subs)))

def ancestors(shape, sub):
    '''list_of_shapes = ancestors(shape, sub)
    Returns the closest ancestors of "sub" in "shape"'''
    def cleanup(shape):
        s = str(shape)
        ss = s.split()[0]
        return ss.split('<')[1]
    shd = (Part.Vertex,
           Part.Edge,
           Part.Wire,
           Part.Face,
           Part.Shell,
           Part.Solid,
           Part.CompSolid,
           Part.Compound)
    for i in range(len(shd)-1):
        if isinstance(sub, shd[i]):
            for j in range(i+1,len(shd)):
                manc = shape.ancestorsOfType(sub, shd[j])
                if manc:
                    print("{} belongs to {} {}.".format(cleanup(sub), len(manc), cleanup(manc[0])))
                    return manc

def rootNode(shape, mode=2, deviation=0.3, angle=0.4):
    buf = shape.writeInventor(mode, deviation, angle)
    from pivy import coin
    inp = coin.SoInput()
    inp.setBuffer(buf)
    node = coin.SoDB.readAll(inp)
    return node

def ruled_surface(e1,e2):
    """ creates a ruled surface between 2 edges, with automatic orientation."""
    import Part
    if not same_direction(e1,e2):
        e = e2.copy()
        e.reverse()
        return Part.makeRuledSurface(e1,e)
    else:
        return Part.makeRuledSurface(e1,e2)

def anim(obj, path, on_path=False, reverse=False, duration=1.0, samples=100):
    """
    Animate obj along path

    anim(obj, path, on_path=False, duration=1.0, samples=100)

    path must be an edge or a wire

    if on_path is True, the animation path is absolute
    else, the animation path is relative to current obj placement

    reverse : reverse path direction

    duration : animation duration in seconds

    samples : number of animation samples
    """
    from time import sleep
    pts = path.discretize(samples)
    if reverse:
        pts.reverse()
    rpts = [p-pts[0] for p in pts]
    if not on_path:
        origin = obj.Placement.Base
    else:
        origin = pts[0]
    for p in rpts:
        obj.Placement.Base = origin + p
        Gui.ActiveDocument.update()
        sleep(float(duration) / samples)




class SilentFPO:
    '''Fake FeaturePython object that has no interaction with other FreeCAD objects.
    It is used as a temporary FPO during editing'''
    def __init__(self):
        self.Proxy = None
        self.Shape = None
        self.props = []
    def addProperty(ptype, pname, pgroup="", pdoc=""):
        setattr(self, pname, None)
        self.props.append(pname)
        return self
    def get_data(self, realfpo):
        for prop in self.props:
            setattr(self, pname, getattr(realfpo, prop))
    def set_data(self, realfpo):
        for prop in self.props:
            setattr(realfpo, pname, getattr(self, prop))
    def status(self):
        for prop in self.props:
            print("%s = %s"%(prop, str(getattr(self, prop))))



class EasyProxy(object):
    def __init__(self, fp):
        self.document_restored = True
        self.ep_add_properties(fp)
        fp.Proxy = self
        self.ep_init(fp)

    def execute(self, fp):
        if not self.document_restored:
            debug("Skipping %s.execute() ..."%fp.Label)
            return False
        else:
            self.ep_execute(fp)

    def onChanged(self, fp, prop):
        if not self.document_restored:
            debug("Skipping %s.onChanged(%s) ..."%(fp.Label,prop))
            return False
        else:
            self.ep_prop_changed(fp, prop)

    def onBeforeChange(self, fp, prop):
        if prop == "Proxy":
            return False
        if not self.document_restored:
            debug("Skipping %s.onBeforeChange(%s) ..."%(fp.Label,prop))
            return False
        else:
            self.ep_before_prop_change(fp, prop)

    def onDocumentRestored(self, fp):
        self.document_restored = True
        debug("%s restored !"%fp.Label)
        self.ep_init(fp)

    def __getstate__(self):
        debug("EasyProxy.__getstate__")
        state = self.ep_on_save()
        # add additional instance variables
        # state["variable"] = self.variable
        return state

    def __setstate__(self,state):
        debug("EasyProxy.__setstate__")
        self.document_restored = False
        self.ep_on_restore(state)
        # restore additional instance variables
        # self.variable = state["variable"]
        return None

    def ep_add_properties(self, fp):
        #fp.addProperty("App::PropertyInteger", "myprop", "Test", "a property").myprop = 1
        return None

    def ep_init(self, fp):
        return None

    def ep_execute(self, fp):
        return None

    def ep_prop_changed(self, fp, prop):
        return None

    def ep_before_prop_change(self, fp, prop):
        return None

    def ep_on_save(self):
        return dict()

    def ep_on_restore(self, state):
        return None



class MyProxy(EasyProxy):

    def ep_add_properties(self, fp):
        debug("---MyProxy.ep_add_properties")
        fp.addProperty("App::PropertyVector", "position", "Test", "a property")
        fp.addProperty("App::PropertyVector", "direction", "Test", "a property")
        fp.addProperty("App::PropertyFloat", "Length", "Test", "a property").Length = 10.0
        fp.addProperty("App::PropertyFloat", "Width", "Test", "a property").Width = 5.0
        fp.addProperty("App::PropertyFloat", "Height", "Test", "a property").Height = 1.0

    def ep_init(self, fp):
        debug("---MyProxy.ep_init(%s)"%fp.Label)

    def ep_execute(self, fp):
        debug("---MyProxy.ep_execute(%s)"%fp.Label)

    def ep_prop_changed(self, fp, prop):
        debug("---MyProxy.ep_prop_changed: %s(%s)"%(fp.Label,prop))

    def ep_before_prop_change(self, fp, prop):
        debug("---MyProxy.ep_before_prop_change: %s(%s)"%(fp.Label,prop))

    def ep_on_save(self):
        debug("---MyProxy.ep_on_save")
        return None

    def ep_on_restore(self,state):
        debug("---MyProxy.ep_on_restore")
        return None

