#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from tests.test_dummy import TestStringMethods
from tests.test_mixed_curve_freecad import TestMixedCurveWithFreeCAD
