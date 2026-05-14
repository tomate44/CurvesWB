import Part
from freecad.Curves.lib.logger import FCLogger

logger = FCLogger("Debug", "lib/face_builder")


def face_validate(face):
    "Tries to fix a non-valid face"
    if face.isValid():
        return face
    try:
        face.validate()
    except Part.OCCError:
        pass
    if face.isValid():
        logger.debug("face validate success.")
    else:
        logger.debug("face validate failed.")
    return face


def shapefix_builder(surface, wires=[], tol=1e-7):
    """
    Create a face with surface and wires
    It uses Part.Shapefix.Face tool.
    new_face = shapefix_builder(face, surface=[], tol=1e-7)
    """
    ffix = Part.ShapeFix.Face(surface, tol)
    for w in wires:
        ffix.add(w)
    ffix.perform()
    if ffix.fixOrientation():
        logger.debug("fixed Orientation")
    if ffix.fixMissingSeam():
        logger.debug("fixed Missing Seam")
    return face_validate(ffix.face())


def change_surface(surface, face, tol=1e-7):
    """
    Create a face with a new surface support
    new_face = change_surface(surface, face, tol=1e-7)
    """
    wires = []
    for w in face.Wires:
        edges = []
        seam_found = False
        for de in w.Edges:
            try:
                e = de.Curve.toShape(de.FirstParameter, de.LastParameter)
                e.Orientation = de.Orientation
            except TypeError:
                e = de
                Part.show(e, "Curve Type Error")
            if e.isSeam(face):
                seam_found = True
            elif e.Length > tol:
                edges.append(e)
        if not seam_found:
            wires.append(Part.Wire(edges))
        else:
            se = Part.sortEdges(edges, tol)
            for el in se:
                wires.append(Part.Wire(el))
    return shapefix_builder(surface, wires, tol)



