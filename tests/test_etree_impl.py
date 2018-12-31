import unittest
import sys
sys.path.append('soho')
from haps import etree_impl as et

class TestElement(et.Element):
    def __init__(self, *args, **kwargs):
        super(TestElement, self).__init__(*args, **kwargs)

class EtreeImplTestCase(unittest.TestCase):
    def setUp(self):
        pass 
    def test_Element_creation(self):
        element = TestElement()

        self.assertIsNotNone(element[element.attribute_token], "attributes map should be present on empty object")
        self.assertEqual(element[element.attribute_token], {}, 'attributes map should be empty at this point')

    def test_attributes_accesor(self):
        element = TestElement()
        self.assertEqual(element[element.attribute_token], element.attributes)
        self.assertTrue((id(element[element.attribute_token]) == id(element.attributes)))

    def test_Element_name_on_creation(self):
        element1 = TestElement('etree_impl')
        element2 = TestElement(name='etree_impl')
        self.assertEqual(element1, element2)
        self.assertEqual(element1.attributes, {'name': 'etree_impl'})
        self.assertEqual(element2.attributes, {'name': 'etree_impl'})

    def test_adding_attributes_on_creation(self):
        element = TestElement('etree_impl', test_attribute='test_value')
        self.assertEqual(element.attributes, {'name':'etree_impl', 'test_attribute':'test_value'},
            "test_attribute should be test_value")

    def test_assertion_attribute_name_always_present(self):
        # FIXME: This is actually a bug
        # Either non-names should be allowed here (and enforced by HapsObj)
        # or __init__(name) NOT __init__(name=None)
        # Actually this whole reference objects by its name should me moved higher
        element1 = TestElement()
        with self.assertRaises(Exception):
            element2 = TestElement(name='etree_impl', first_element=element1)

        print "This case should not pass. FIXME"



    def test_referencing_elements_by_name(self):
        # see above
        element1 = TestElement('first_element')
        element2 = TestElement('second_element', second_element=element1)
        element3 = TestElement('second_element', second_element='first_element')
        self.assertEqual(element2, element3, "")


    def test_tag(self):
        element1 = TestElement()
        element2 = et.Element()
        self.assertEqual(element1.tag, TestElement.__name__.lower(), 
            "Element tag should match lowercase of its class name")
        self.assertNotEqual(element1.tag, element2.tag, 
            'Instances of two classes should have different tags.')

    def test_setting_attributes(self):
        element1 = TestElement()
        element1.set('test_attribute', 'test_value')
        self.assertEqual(element1.attributes, {'test_attribute': 'test_value'})

    def test_getting_attributes(self):
        element1 = TestElement()
        element1.set('test_attribute', 'test_value')
        self.assertEqual(element1.get('test_attribute'),  'test_value')

    def test_text_attribute(self):
        element1 = TestElement()
        element1.set('text', 'test_text')
        self.assertEqual(element1.text,  'test_text')

    def test_data_accesor(self):
        element1 = TestElement()
        element1.set('text', 'test_text')
        self.assertEqual(element1.data,  'test_text')
        self.assertEqual(element1.text, element1.data)

    def test_append_element(self):
        element1 = TestElement()
        element2 = TestElement()
        element1.append(element2)
        typename = TestElement.__name__.lower()
        self.assertTrue(isinstance(element1[typename] , list))
        self.assertEqual(element1[typename], [element2])

    def test_append_None(self):
        element1 = TestElement()
        element2 = element1.append(None)
        self.assertEqual(element1, element2)
        self.assertEqual(id(element1), id(element2))

    def test_append_not_Elemenet_or_None(self):
        element1   = TestElement()
        nonelement = list()
        with self.assertRaises(AssertionError):
            element1.append(nonelement)

    def test_extend(self):
        element1 = TestElement()
        elements = [TestElement() for element in range(2)]
        element1.extend(elements)
        typename = TestElement.__name__.lower()
        self.assertEqual(element1[typename], [TestElement() for element in range(2)]) 

    def test_find(self):
        element1 = TestElement()
        elements = [TestElement() for element in range(2)]
        element1.extend(elements)
        typename = TestElement.__name__.lower()
        self.assertEqual(element1.find(typename), elements[0])

    def test_findall(self):
        element1 = TestElement()
        elements = [TestElement() for element in range(2)]
        element1.extend(elements)
        typename = TestElement.__name__.lower()
        self.assertEqual(element1.findall(typename), elements)

    def test_remove(self):
        element1 = TestElement()
        elements = [TestElement() for element in range(2)]
        element1.extend(elements)
        typename = TestElement.__name__.lower()
        removed = element1.remove(elements[0])
        self.assertEqual(removed, elements[0])
        self.assertEqual(element1[typename], elements[1:])
        self.assertEqual(id(removed), id(elements[0]))

    def test_keys(self):
        # keys() hides xml attributes and returns only children by typename
        element1 = TestElement('test_name', some_attribite='some_value')
        element2 = TestElement()
        element1.append(element2)
        self.assertNotEqual(element1.keys() , ['name', 'some_attribite'])
        self.assertEqual(element1.keys(), [element2])

    def test_tojson(self):
        element1 = TestElement('test_name', some_attribite='some_value')
        element2 = TestElement()
        element1.append(element2)
        print "This case should not pass. FIXME"

        # self.assertIsNotNone(element1.tojson(indent=0))

    def test_toxml(self):
        # note the bug (extra spaces and new line with pretty_print=False)
        from StringIO import StringIO
        test_xml=' <testelement name="test_name" some_attribite="some_value">    <element/>\n </testelement>'
        element1 = TestElement('test_name', some_attribite='some_value')
        element2 = et.Element()
        element1.append(element2)
        fileio = StringIO()
        xml = element1.toxml(fileio, pretty_print=False)
        self.assertEqual(xml.getvalue(), test_xml)
        print "This case should not pass. FIXME"















