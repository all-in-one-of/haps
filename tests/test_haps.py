import unittest
import sys
sys.path.append('soho')
from haps import HapsObj
from haps.tags import Parameter

class TestObject1(HapsObj):
    def __init__(self, *args, **kwargs):
        super(TestObject1, self).__init__(*args, **kwargs)

class TestObject2(HapsObj):
    def __init__(self, *args, **kwargs):
        super(TestObject2, self).__init__(*args, **kwargs)

class HapsObjTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def test_HapsObj_creation(self):
        obj = HapsObj('test_object', some_attribute='some_value')
        self.assertEqual(obj.get('name'), 'test_object')
        self.assertEqual(obj.get('some_attribute'), 'some_value')

    def test_add_object(self):
        obj1 = HapsObj('test_object1', some_attribute='some_value')
        obj2 = HapsObj('test_object2', some_attribute='some_value')
        obj1.add(obj2)
        self.assertEqual(obj1.find('hapsobj'), obj2)

    def test_add_multiply_objects_by_list_or_tuple(self):
        obj1 = HapsObj('test_object1', some_attribute='some_value')
        obj2 = HapsObj('test_object2', some_attribute='some_value')
        obj3 = HapsObj('test_object3', some_attribute='some_value')
        obj1.add([obj2, obj3])
        self.assertEqual(obj1.findall('hapsobj'), [obj2, obj3])
        obj4 = HapsObj('test_object4', some_attribute='some_value')
        obj4.add((obj2, obj3))
        self.assertEqual(obj1.findall('hapsobj'), obj4.findall('hapsobj'))

    def test_tostring(self):
        # FIXME: newline
        temp = '<hapsobj some_attribute="some_value" name="test_object1"/>\n'
        obj1 = HapsObj('test_object1', some_attribute='some_value')
        self.assertEqual(str(obj1), temp)
        print "This case should not pass. FIXME"


    def test_add_parms(self):
        # TODO: more cases 
        obj1 = HapsObj('test_object1', some_attribute='some_value')
        parm_template = (('parm1', 'value1'), ('parm2', 'value2'))
        parm_instance = [Parameter('parm1', 'value1'), Parameter('parm2', 'value2')]

        obj1.add_parms(parm_template)
        self.assertEqual(obj1.findall("parameter"), parm_instance)

    def test_get_by_type(self):
        obj1 = TestObject1('test_object1')
        obj2 = TestObject1('test_object2')
        obj3 = TestObject2('test_object3')
        obj1.add(obj2)
        obj1.add(obj3)
        self.assertEqual(obj1.get_by_type('testobject1'), [obj2])
        self.assertEqual(obj1.get_by_type('testobject2'), [obj3])
        self.assertNotEqual(obj1.get_by_type('testobject1'), obj1.get_by_type('testobject2'))

    def test_get_by_name(self):
        obj1 = TestObject1('test_object1')
        obj2 = TestObject1('test_object2')
        obj3 = TestObject2('test_object3')
        obj1.add(obj2)
        obj1.add(obj3)
        self.assertEqual(obj1.get_by_name('test_object2'), obj2)
        self.assertEqual(obj1.get_by_name('test_object3'), obj3)
        self.assertNotEqual(obj1.get_by_name('test_object2'), obj1.get_by_name('test_object3'))

    def test_get_by_name_and_type(self):
        obj1 = TestObject1('test_object1')
        obj2 = TestObject1('test_object2')
        obj3 = TestObject2('test_object2') # same name, different type
        obj1.add(obj2)
        obj1.add(obj3)

        self.assertEqual(obj1.get_by_name('test_object2', typename='testobject1'), obj2)
        self.assertEqual(obj1.get_by_name('test_object2', typename='testobject2'), obj3)

























