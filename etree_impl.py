import collections, types
from collections import defaultdict, OrderedDict

HAPS_DEBUG=True

class XMLTokens(defaultdict):
    text_template    ='{nl}{wh}{text}{nl}{wh2}{start}{tag}{end}'
    element_template = '{wh}{start}{tag}{attrib}{end}{text}{nl}'
    start_tag = '<'
    end_tag   = '/>'
    parent_end_tag = '>'
    parent_start_tag='</'


class Element(OrderedDict):
    """Minimal implementation of xml.ElementTree API
       based on Python native dictionary.
    """
    attribute_token = '@attrib'
    
    def __init__(self, name=None, **kwargs):
        """Init object with attribs from kwargs."""
        super(Element, self).__init__()

        self[self.attribute_token] = {}

        if name:
            self.attributes['name'] = name

        for k,v in kwargs.items():
            # Turn Haps object into its name:
            if isinstance(v, Element):
                if 'name' in v.attributes:
                    v = v.attributes['name']
                elif HAPS_DEBUG:
                    raise Exception('Attribute "%s" \
                        not present on object %s' % ('name', v))
            self[self.attribute_token][k] = v

    def __iter__(self):
        for key, values in [(k, self[k]) for k \
            in super(Element, self).__iter__()]:
            if key == self.attribute_token:
                continue
            for v in values:
                yield v 

    def __str__(self):
        """ Major functionality of this class. Using base clase to tostring() method
            represents itself as a XML node / document.
        """
        return self.tostring()

    def __repr__(self):
        return super(Element, self).__repr__()

    @property
    def attributes(self):
        return self[self.attribute_token]

    @property
    def tag(self):
        return type(self).__name__.lower()

    @property 
    def text(self):
        if 'text' in self[self.attribute_token]:
            return self[self.attribute_token]['text']
        return ''

    @property
    def data(self):
        return self.text

    def append(self, obj):
        """Add child element to current parent.

        :parm:   obj is an object of the same type as self.
        :return: self 
        """
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

    def get(self, attribute, raise_on_fail=True):
        """Get attribute from self .

        :parm attribute:     Name of an attribute to return
        :parm raise_on_fail: If True nonexsting attribute query will raise an Exception
        :returns:            Attribute value or None (with raise_on_fail=False)
        """
        if attribute in self.attributes:
            return self[self.attribute_token][attribute]
        elif raise_on_fail:
            raise Exception('Attribute "%s" not present on object %s' % (attribute, self))
        return None

    def find(self, tag, _all=False):
        """Find first child element of type: tag. Only 
        first element of a type 'tag' will be returend. Use findall
        to search for multiply elements of the 'tag'.

        :parm tag: the name of the type of element type to be returned.
        "returns : First child of type 'tag'.
        """
        if tag in self and tag != self.attribute_token:
            if len(self[tag]):
                return self[tag] if _all else self[tag][0]
        return None

    def findall(self, tag):
        """Find all children elements of a given type (tag).
        :parm tag: the name of the type of elements to be returned.
        """
        children = self.find(tag, _all=True)
        if children:
            return children
        return []

    def remove(self, obj):
        """Remove element from a children list."""
        typename = type(obj).__name__.lower()
        assert(obj in self[typename])
        index = self[typename].index(obj)
        return self[typename].pop(index)

    def keys(self):
        """Return a list of attributes of the element."""
        return [key for key in super(Element, self).keys() \
            if key != self.attribute_token]

    def set(self, key, value):
        """Sets a value of the attribute. """
        if not self.attribute_token in self:
            self[self.attribute_token] = {}
        self[self.attribute_token][key] = value

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
        :returns:           fileio object
        """
        def whitespace(level, indent=4, whs=' ', pprint=True):
            if pretty_print:
                return whs * indent * level
            return whs

        def trim_lines(items, length=4, lines=[]):
            lines += [' '.join(map(str, items[start:start+length])) 
                for start in range(0, len(items), length)]
            return lines

        def _attributes_to_string():
            attributes_map = ['{}="{}"'.format(k,v) for k,v in self.attributes.items()
                if k != 'text'] 
            return ' ' + ' '.join(attributes_map)

        attributes = _attributes_to_string() if self.attributes else ''
        new_line   = '' if not pretty_print else '\n'
        pp = pretty_print

    
        if not list(self) and not self.text:
            etag = XMLTokens.end_tag
        else:
            etag = XMLTokens.parent_end_tag

        text  = ''
        if self.text:
            text = '{}{}'.format(new_line, whitespace(_level+1, indent=indent, pprint=pp))
            text = text.join(trim_lines(self.text, length=4))
            text = XMLTokens.text_template.format(wh=whitespace(_level+1, indent=indent, pprint=pp), 
                text=text, start=XMLTokens.parent_start_tag, wh2=whitespace(_level, indent=indent, pprint=pp),
                tag=self.tag, end=XMLTokens.parent_end_tag, nl=new_line)

        xml_token = XMLTokens.element_template.format(wh=whitespace(_level, indent=indent, pprint=pp),
            start=XMLTokens.start_tag, tag=self.tag, attrib=attributes, end=etag, 
            text=text, nl=new_line)

        # Open tag
        fileio.write(xml_token)
        
        for child in self:
            # FIXME: Bug is here:
            if isinstance(child, Element):
                child.toxml(fileio, indent=indent, _level=_level+1)

        if etag == XMLTokens.parent_end_tag and not self.text:
            xml_token = XMLTokens.element_template.format(wh=whitespace(_level, indent=indent, pprint=pp),
                start=XMLTokens.parent_start_tag, tag=self.tag, end=XMLTokens.parent_end_tag, attrib='',
                text='', nl=new_line)
            # Close tag
            fileio.write(xml_token)

        return fileio




