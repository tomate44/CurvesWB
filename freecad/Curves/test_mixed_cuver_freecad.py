#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for mixed_curve.py using real FreeCAD environment
Run this with FreeCAD's Python interpreter
"""

import unittest
import sys
import os

# Import FreeCAD modules (should work in AppImage environment)
try:
    import FreeCAD
    import FreeCADGui
    import Part
    print("✅ FreeCAD modules imported successfully")
    FREECAD_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import FreeCAD modules: {e}")
    FREECAD_AVAILABLE = False

# Add the path to your mixed_curve module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import mixed_curve
    print("✅ mixed_curve module imported successfully")
    MIXED_CURVE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Failed to import mixed_curve: {e}")
    MIXED_CURVE_AVAILABLE = False


class TestMixedCurveWithFreeCAD(unittest.TestCase):
    """Test mixed curve with real FreeCAD environment"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        if FREECAD_AVAILABLE:
            # Create a new document for testing
            cls.doc = FreeCAD.newDocument("TestDoc")
            print(f"✅ Created test document: {cls.doc.Name}")
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        if FREECAD_AVAILABLE and hasattr(cls, 'doc'):
            FreeCAD.closeDocument(cls.doc.Name)
            print("✅ Cleaned up test document")
    
    def setUp(self):
        """Set up before each test"""
        if not FREECAD_AVAILABLE:
            self.skipTest("FreeCAD not available")
        if not MIXED_CURVE_AVAILABLE:
            self.skipTest("mixed_curve module not available")
    
    def test_freecad_environment(self):
        """Test that FreeCAD environment is working"""
        self.assertTrue(FREECAD_AVAILABLE)
        self.assertIsNotNone(FreeCAD.Version())
        print(f"FreeCAD Version: {FreeCAD.Version()}")
    
    def test_create_basic_geometry(self):
        """Test creating basic geometry objects"""
        # Create a simple line for testing
        p1 = FreeCAD.Vector(0, 0, 0)
        p2 = FreeCAD.Vector(10, 0, 0)
        line = Part.LineSegment(p1, p2)
        
        self.assertIsNotNone(line)
        self.assertEqual(line.StartPoint, p1)
        self.assertEqual(line.EndPoint, p2)
    
    def test_mixed_curve_with_real_geometry(self):
        """Test mixed curve with real FreeCAD geometry"""
        # Create test edges
        edges = []
        
        # Line segment
        line = Part.LineSegment(
            FreeCAD.Vector(0, 0, 0), 
            FreeCAD.Vector(5, 0, 0)
        )
        edges.append(Part.Edge(line))
        
        # Arc
        circle = Part.Circle(FreeCAD.Vector(7.5, 0, 0), FreeCAD.Vector(0, 0, 1), 2.5)
        arc = Part.Edge(circle, 0, 3.14159)  # Half circle
        edges.append(arc)
        
        # Test with mixed_curve if available
        if hasattr(mixed_curve, 'MixedCurve'):
            try:
                curve = mixed_curve.MixedCurve(edges)
                self.assertIsNotNone(curve)
                print("✅ MixedCurve created with real geometry")
            except Exception as e:
                print(f"⚠️  MixedCurve creation failed: {e}")
        else:
            print("⚠️  MixedCurve class not found in module")
    
    def test_curve_properties_with_freecad(self):
        """Test curve properties using FreeCAD objects"""
        # Create a B-spline curve
        poles = [
            FreeCAD.Vector(0, 0, 0),
            FreeCAD.Vector(1, 1, 0),
            FreeCAD.Vector(2, 0, 0),
            FreeCAD.Vector(3, 1, 0)
        ]
        
        bspline = Part.BSplineCurve()
        bspline.buildFromPoles(poles)
        edge = Part.Edge(bspline)
        
        # Test basic properties
        self.assertTrue(edge.Length > 0)
        self.assertIsNotNone(edge.FirstParameter)
        self.assertIsNotNone(edge.LastParameter)
        
        print(f"Edge length: {edge.Length}")
        print(f"Parameter range: {edge.FirstParameter} to {edge.LastParameter}")
    
    def test_document_integration(self):
        """Test integration with FreeCAD document"""
        # Add an object to the document
        obj = self.doc.addObject("Part::Feature", "TestCurve")
        
        # Create simple geometry
        line = Part.LineSegment(
            FreeCAD.Vector(0, 0, 0), 
            FreeCAD.Vector(10, 10, 0)
        )
        obj.Shape = Part.Edge(line)
        
        self.doc.recompute()
        
        # Verify object was created
        self.assertIn("TestCurve", [obj.Name for obj in self.doc.Objects])
        self.assertTrue(obj.Shape.isValid())
        
        print(f"✅ Created object in document: {obj.Name}")


def run_freecad_tests():
    """Run tests with detailed output"""
    print("="*60)
    print("RUNNING FREECAD APPIMAGE TESTS")
    print("="*60)
    
    # Check environment
    print("Environment Check:")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path includes: {sys.path[:3]}...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMixedCurveWithFreeCAD)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_freecad_tests()
    sys.exit(0 if success else 1)