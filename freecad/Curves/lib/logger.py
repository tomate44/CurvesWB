# SPDX-License-Identifier: LGPL-2.1-or-later

import sys
from FreeCAD import Console, Vector
import Part


class FCLogger:
    """
    Logging tool for FreeCAD Console
    Example:
    logger = FCLogger(level="Debug", name="MyLogger")
    logger.warn("This is a warning")
    logger.debug("Debug info")
    """
    levels = {"Critical": 0,
              "Error": 1,
              "Warning": 2,
              "Info": 3,
              "Debug": 4}

    def __init__(self, level="Error", name=None):
        self.name = name
        self.Level = level
        self.IncludeFuncName = True
        self.NbDecimal = 4

    def current_func_name(n=0, it=5):
        names = []
        fn = ""
        for i in range(it):
            try:
                fn = sys._getframe(i + n + 1).f_code.co_name
            except ValueError:
                break
            if fn == "<module>":
                break
            names.append(fn)
        return ".".join(names[::-1])

    def rank(level):
        return FCLogger.levels[level]

    def strconv(self, dat):
        "Conversion of various data types to string"
        nb = self.NbDecimal
        if isinstance(dat, Vector):
            return f"Vector ({dat.x:.{nb}f}, {dat.y:.{nb}f}, {dat.z:.{nb}f})"
        elif isinstance(dat, Part.Vertex):
            return self.strconv(dat.Point)
        else:
            return str(dat)

    def strform(self, dat, pre="", post=""):
        strl = [self.strconv(arg) for arg in dat]
        string = " ".join(strl)
        return pre + string + post + "\n"

    def process(self, *args, **kwargs):
        func = kwargs["func"]
        pre = ""
        if self.IncludeFuncName:
            try:
                func(f"-> {self.name} " + FCLogger.current_func_name(2) + "\n")
                pre = "   "
            except ValueError:
                pass
        func(self.strform(args, pre))

    def debug(self, *args):
        if FCLogger.rank(self.Level) < FCLogger.rank("Debug"):
            return
        self.process(*args, func=Console.PrintMessage)

    def info(self, *args):
        if FCLogger.rank(self.Level) < FCLogger.rank("Info"):
            return
        self.process(*args, func=Console.PrintMessage)

    def warn(self, *args):
        if FCLogger.rank(self.Level) < FCLogger.rank("Warning"):
            return
        self.process(*args, func=Console.PrintWarning)

    def error(self, *args):
        if FCLogger.rank(self.Level) < FCLogger.rank("Error"):
            return
        self.process(*args, func=Console.PrintError)

    def critic(self, *args):
        if FCLogger.rank(self.Level) < FCLogger.rank("Critical"):
            return
        self.process(*args, func=Console.PrintCritical)


# log = FCLogger("Debug")
# log.info("Coucou")
# log.debug("Debug")
# log.warn("Warning")
# log.error("Error")
# log.critic("Critical")
#
# v = Vector(1.00000000000001,0,0)
# log.debug(v, Part.Vertex(v))
