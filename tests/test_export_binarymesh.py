import time
import tempfile
import os
import unittest

class BinaryMeshTestCase(unittest.TestCase):
    binarymesh = None

    def setUp(self):
        try:
            import hou
        except:
            self.skipTest("Can't proceed without hou module.")

        geo  = hou.node('/obj').createNode("geo")
        self.box = geo.createNode('box')

    def tearDown(self):
        if os.path.exists(self.binarymesh):
            os.unlink(self.binarymesh)

    def test_exportBinaryMesh(self):
        clockstart = time.time()
        self.binarymesh = os.path.join(tempfile.gettempdir(), 
            tempfile.gettempprefix() + '.binarymesh')
        self.box.geometry().saveToFile(self.binarymesh)
        print('Export time: %g seconds' % (time.time() - clockstart))
        self.assertTrue(os.path.exists(self.binarymesh))

