import unittest


class BaseTestCase(unittest.TestCase):
    """Base class for testing FreeCAD environment"""

    def setUp(self):
        print(f"  ▶️ Run test {self._testMethodName}")
