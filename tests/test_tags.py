import unittest
import sys
sys.path.append('soho')
from haps.tags import *


class HapsTagsTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def test_Matrix_default_init(self):
        mat = Matrix()
        self.assertEqual(mat.identity, mat.text)

    def test_Matrix_init(self):
        arg = (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)
        mat = Matrix(arg)
        self.assertEqual(arg, mat.text)

    def test_Matrix_wrong_init(self):
        arg = (1,2,3,4,5,3,14,15,16) # too short
        with self.assertRaises(AssertionError):
            mat = Matrix(arg)

    def test_Values_init(self):
        v = Values([1, 2, 3])
        self.assertEqual(v.text, [1,2,3])

    def test_Alpha_init(self):
        v = Alpha([1])
        self.assertEqual(v.text, [1])

    def test_Alpha_wrong_init(self):
        with self.assertRaises(AssertionError):
            v = Alpha(1)
        with self.assertRaises(AssertionError):
            v = Alpha([1,2,3])

    def test_Parameter_init(self):
        parm = Parameter('some_name', 'some_value')
        self.assertEqual(parm.get('name'), 'some_name')
        self.assertEqual(parm.get('value'), 'some_value')
        # FIXME: this is bug as None value shouldn't be allowed

    def test_Parameter_wrong_init(self):
        parm = Parameter('some_name')
        self.assertEqual(parm.get('name'), 'some_name')
        with self.assertRaises(Exception):
            print "This case should not pass. FIXME"
            self.assertEqual(parm.get('value'), None)

    def test_Parameters_init(self):
        parms = Parameters('some_name')
        self.assertEqual(parms.get('name'), 'some_name')

    def test_Transform_init(self):
        xform = Transform(0.5)
        self.assertEqual(xform.get('time'), 0.5)

    def test_Project_init(self):
        project = Project()
        self.assertEqual(project.get('format_revision'), FORMAT_REVISION)







