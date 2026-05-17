# SPDX-License-Identifier: LGPL-2.1-or-later

from FreeCAD import Console
import time


def timer(logger=None):
    'Timer decorator for normal functions'
    def timerdec(func):
        def wrapper_timer(*args, **kwargs):
            tic = time.perf_counter()
            value = func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            mess = f"{func.__name__}: {elapsed_time:0.4f} seconds"
            if logger is None:
                Console.PrintMessage(mess + "\n")
            else:
                logger.info(mess)
            return value
        return wrapper_timer
    return timerdec


def cls_timer(func):
    'Timer decorator for class methods'

    def wrapper_timer(self, *args, **kwargs):
        tic = time.perf_counter()
        value = func(self, *args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        mess = f"{func.__name__}: {elapsed_time:0.4f} seconds"
        if not hasattr(self, "log"):
            Console.PrintMessage(mess + "\n")
        else:
            self.log.info(mess)
        return value
    return wrapper_timer
