import time
import tempfile
import os
import unittest

class BinaryMeshTestCase(unittest.TestCase):
    houdini_available = False
    binarymesh = None
    def setUp(self):
        try:
            import hou
            self.box = hou.node("/obj/box/OUT")
            self.houdini_available = True
        except:
            self.skipTest("Can't proceed without hou module.")

    def tearDown(self):
        if not self.houdini_available:
            return
        if os.path.exists(self.binarymesh.name):
            os.unlink(self.binarymesh.name)

    def test_exportBinaryMesh(self):
        clockstart = time.time()
        self.binarymesh = tempfile.NamedTemporaryFile(False)
        self.box.geometry.saveToFile(self.binarymesh+'.binarymesh')
        print('Export time: %g seconds' % (time.time() - clockstart))
        self.assertTrue(os.path.exists(self.binarymesh.name))

