import time
import tempfile
import os
import unittest

class BinaryMeshTestCase(unittest.TestCase):
    binarymesh = None
    primtypes  = {'poly':0, 'polymesh':1, 'mesh': 2, 'nurbs': 3, 'bezier': 4}

    def setUp(self):
        try:
            import hou
        except:
            self.skipTest("Can't proceed without hou module.")

        geo  = hou.node('/obj').createNode("geo")
        self.geometry = geo.createNode('box')
        self.binarymesh = os.path.join(tempfile.gettempdir(), 
            tempfile.gettempprefix() + '.binarymesh')

    def tearDown(self):
        if os.path.exists(self.binarymesh):
            os.unlink(self.binarymesh)

    def run_export_geometry(self, primtype):
        clockstart = time.time()
        self.geometry.parm('type').set(self.primtypes[primtype])
        self.geometry.geometry().saveToFile(self.binarymesh)
        print('Export time for %s: %g seconds' % (primtype, time.time() - clockstart))

    def test_export_polygon(self):
        self.run_export_geometry('poly')  
        self.assertTrue(os.path.exists(self.binarymesh))
        os.unlink(self.binarymesh) 

    def test_export_polymesh(self):
        self.run_export_geometry('polymesh')  
        self.assertTrue(os.path.exists(self.binarymesh))
        os.unlink(self.binarymesh) 

    def test_export_mesh(self):
        self.run_export_geometry('mesh')
        self.assertTrue(os.path.exists(self.binarymesh))
        os.unlink(self.binarymesh)

    def test_export_nurbs(self):
        self.run_export_geometry('nurbs')
        self.assertTrue(os.path.exists(self.binarymesh))
        os.unlink(self.binarymesh)  

    def test_export_bezier(self):
        self.run_export_geometry('bezier')
        self.assertTrue(os.path.exists(self.binarymesh))
        os.unlink(self.binarymesh)        



