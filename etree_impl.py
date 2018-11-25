import collections, types
from collections import defaultdict

class XMLTokens(object):
    text_template    ='{nl}{whitespace}{text}{nl}{whitespace}{start}{tag}{end}'
    element_template = '{whitespace}{start}{tag}{attrib}{end}{text}{nl}'
    start_tag = '<'
    end_tag   = '/>'
    child_tag = '>'


class Element(defaultdict):
    """Minimal implementation of xml.ElementTree API
       based on Python native dictionary.
    """
    attribute_token = '@'
    text_token      = '#'

    def __init__(self, name=None, **kwargs):
        """Init object with attribs from kwargs."""
        if name:
            self.__setattr__('name', name)
        for k,v in kwargs.items():
            # Turn Haps object into its name:
            if isinstance(v, Element):
                v = v[self.attribute_token+'name']
            self.__setattr__(k, v)

    def __setattr__(self, name, value):
        """Maps Python object attribs to xml attribs via @notation in json."""
        if name == self.text_token:
            super(Element, self).__setitem__(self.text_token, value)
        else:
            super(Element, self).__setitem__(self.attribute_token+name, value)

    def __iter__(self):
        for typename, children in self.items():
            if typename.startswith(self.attribute_token):
                continue
            if typename.startswith(self.text_token):
                continue
            for child in children:
                yield child 

    def __repr__(self):
        """ Major functionality of this class. Using base clase to tostring() method
            represents itself as a XML node / document.
        """
        return self.tostring()

    @property
    def tag(self):
        return type(self).__name__.lower()

    @property 
    def text(self):
        if self.text_token in super(Element, self).keys():
            return self[self.text_token]
        return

    @property
    def data(self):
        return self.text

    def append(self, obj):
        """Add child element to current parent.

        :parm:   obj is an object of the same type as self.
        :return: self 
        """
        #FIXME:
        from haps_types import HapsVal

        def _add_value(v):
            typename = type(obj).__name__.lower()
            self[typename] = v

        if isinstance(obj, HapsVal):
            _add_value(obj)
            return self

        # We allow to pass Nones here:
        if obj == None: return self
        assert(isinstance(obj, Element))
        typename = type(obj).__name__.lower()

        if typename in self: 
            self[typename] += [obj]
        else: 
            self[typename] = [obj]
        return self

    def extend(self, objs):
        """Extends element with collection of subelements.

        :parm objs:   list of elements iof type HapsObj to be added as children. 
        :returns:      self
        """
        [self.append(x) for x in objs]
        return self

    def get(self, name, raise_on_fail=True):
        """Get local (self element's) attribute.

        :parm name:          Name of an attribute to return
        :parm raise_on_fail: If True nonexsting attribute query will raise an Exception
        :returns:            Sting with attribute value or None (with raise_on_fail=False)
        """
        attr = self.attribute_token+name
        if attr in self.keys():
            return self[attr]
        elif raise_on_fail:
            raise Exception('Attribute "%s" not present on object %s' % (name, self))
        return None

    def find(self, tag):
        """Find first child element of type name/tag. Only 
        first element of a type 'tag' will be returend. Use findall
        to search for multiply elements of the 'tag'.

        :parm tag: the name of the type of element type to be returned.
        """
        for typename, children in self.items():
            # only children, not attributes
            if not typename.startswith(self.attribute_token)\
                and typename == tag:
                return self[typename][0]
        return None

    def findall(self, tag):
        """Find all children elements of a given type (tag).
        :parm tag: the name of the type of elements to be returned.
        """
        for typename, children in self.items():
            # only children, not attributes
            if not typename.startswith(self.attribute_token)\
                and typename == tag:
                return self[typename]
        return None

    def remove(self, obj):
        """Remove element from a children list."""
        typename = type(obj).__name__.lower()
        assert(obj in self[typename])
        index = self[typename].index(obj)
        return self[typename].pop(index)

    def keys(self):
        """Return a list of attributes of the element."""
        return [key for key in super(Element, self).keys() \
            if key.startswith(self.attribute_token)]

    def set(self, key, value):
        """Sets a value of the attribute. """
        self.__setattr__(key, value)

    def tostring(self, pretty_print=True):
        """Returns xml string of current element and its children."""
        from StringIO import StringIO
        return self.toxml(StringIO()).getvalue()

    def tojson(self, indent=2):
        """Return json representation of current element."""
        from json import dumps
        return dumps(self, indent=indent)

    def toxml(self, fileio, pretty_print=True, indent=4, _level=0):
        """Render element and its children into XML document.

        :parm fileio:       Writeable file-like object (file object, StringIO, sys.stdout etc)
        :parm pretty_print: print with new lines and tabs (default True)
        :parm indent:       Initial indent for pretty print (defualt 0)
        :parm whitespace:   Whitespace used in pretty print (default 4* ' ')
        :returns:           fileio object
        """
        def _attributes_to_string():
            attributes_map = ['{0}="{1}"'.format(
                k.strip(self.attribute_token), 
                str(self[k])) for k in self.keys()]
            return ' ' + ' '.join(attributes_map)

        attributes = _attributes_to_string() if self.keys() else ''

        if pretty_print:
            new_line   = '\n'
            whitespace = ' ' * indent * _level
        else:
            new_line   = ''
            whitespace = ''

        # Some keys aren't attributes (not returned by self.keys())...
        if self.keys() == super(Element, self).keys():
            etag = XMLTokens.end_tag
        else:
            etag = XMLTokens.child_tag

        text  = ''
        if self.text:
            text = XMLTokens.text_template.format(whitespace=whitespace,
                text=' '.join(map(str, self.text)), start=XMLTokens.start_tag, 
                tag=self.tag, end=XMLTokens.end_tag, nl=new_line)

        xml_token = XMLTokens.element_template.format(whitespace=whitespace,
            start=XMLTokens.start_tag, tag=self.tag, attrib=attributes, end=etag, 
            text=text, nl=new_line)

        # Open tag
        fileio.write(xml_token)
        
        for child in self:
            # FIXME: Bug is here:
            if isinstance(child, Element):
                child.toxml(fileio, indent=indent, _level=_level+1)

        if etag == XMLTokens.child_tag and not self.text:
            xml_token = XMLTokens.element_template.format(whitespace=whitespace,
                start=XMLTokens.start_tag, tag=self.tag, end=XMLTokens.end_tag, attrib='',
                text='', nl=new_line)
            # Close tag
            fileio.write(xml_token)

        return fileio




