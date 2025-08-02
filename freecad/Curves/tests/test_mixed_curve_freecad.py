#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for mixed_curve.py using real FreeCAD environment
Run this with FreeCAD's Python interpreter
"""

import os
import sys
import unittest
from pathlib import Path
from pprint import pprint

from freecad.Curves import mixed_curve
from freecad.Curves.tests.base_test import BaseTestCase

# Import FreeCAD modules (should work in AppImage environment)
try:
    import FreeCAD
    import FreeCADGui
    import Part

    print("✅ FreeCAD modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import FreeCAD modules: {e}")
    exit(1)

# Add the path to your mixed_curve module
currentFilePath = Path(__file__)
moduleDir = currentFilePath.parent.parent.absolute()
sys.path.append(f"{moduleDir}")

try:
    import freecad.Curves.mixed_curve
    print("✅ mixed_curve module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import mixed_curve: {e}")
    exit(1)


class TestMixedCurveWithFreeCAD(BaseTestCase):
    """Test mixed curve with real FreeCAD environment"""

    MODULE = "test_mixed_curve_freecad"

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Create a new document for testing
        cls.doc = FreeCAD.newDocument("TestDoc")
        print(f"✅ Created test document: {cls.doc.Name}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        if hasattr(cls, 'doc'):
            FreeCAD.closeDocument(cls.doc.Name)
            print("✅ Cleaned up test document")

    def setUp(self):
        """Set up before each test"""
        BaseTestCase.setUp(self)

    def test_freecad_environment(self):
        """Test that FreeCAD environment is working"""
        self.assertIsNotNone(FreeCAD.Version())
        print(f"FreeCAD Version: {FreeCAD.Version()}")

    def test_creation_curve_from_file_with_sketches(self):
        """Test curves from file freecad/Curves/TestFiles/gtr.FCStd"""
        import glob
        import os

        test_file = "./freecad/Curves/TestFiles/gtr.FCStd"

        file_name = os.path.basename(test_file)
        print(f"  Loading test file: {file_name}")

        doc = FreeCAD.openDocument(test_file)
        self.assertIsNotNone(doc)
        self.assertIsNotNone(doc.Name)

        sketches = []
        for obj in doc.Objects:
            if obj.Name == "Sketch039" or obj.Name == "Sketch040":
                # add sketch for create a new working curve
                sketches.append(obj)
            elif obj.Name == "Mixed_curve018" or obj.Name == "Mixed_curve019":
                # check, that we have 2 bad curves
                self.assertEqual(len(obj.Shape.Wires), 0)

        self.assertEqual(len(sketches), 2)

        curve = mixed_curve.MixedCurveCmd().makeCPCFeature(
            sketches[0], sketches[1], 
            mixed_curve.MixedCurveCmd().get_sketch_plane_normal(sketches[0]),
            mixed_curve.MixedCurveCmd().get_sketch_plane_normal(sketches[1])
        )
        # check, that new wire is ok and will be rendered without errors
        self.assertGreater(len(curve.Shape.Wires), 0)

        recomputeRes = doc.recompute()        
        FreeCAD.closeDocument(doc.Name)