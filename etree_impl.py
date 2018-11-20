import collections, types
from collections import defaultdict
from StringIO import StringIO


class Element(defaultdict):
    """Minimal implementation of xml.ElementTree API
       based on Python native dictionary.
    """
    #FIXME: Changing this causes a bug (some of the attribs names are swollowed)
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
            # Collapse iterrables to string:
            elif isinstance(v, collections.Iterable) and \
            not  isinstance(v, types.StringTypes):
                v = ' '.join(map(str, v))
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
            # FIXME: HapsVal was a mistake
            # if isinstance(children, collections.Iterable):
                # continue
                # yield children
            for child in children:
                yield child 

    def __repr__(self):
        """ Major functionality of this class. Using base clase to tostring() method
            represents itself as a XML node / document.
        """
        root=type(self).__name__.lower()
        return self.tostring(root=root)

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

        :parm tag: the name of the type of element type to be returned. """
        for typename, children in self.items():
            # only children, not attributes
            if not typename.startswith(self.attribute_token)\
                and typename == tag:
                # This is special case for HpasVal TODO: Make it more natural
                if  type(self[typename][0]) in (type(1), type(1.0)):
                    return self[typename]
                return self[typename][0]
        return None

    def findall(self, tag):
        """Finds all children elements of a given type (tag).
        :parm tag: the name of the type of elements to be returned."""
        for typename, children in self.items():
            # only children, not attributes
            if not typename.startswith(self.attribute_token)\
                and typename == tag:
                return self[typename]
        return None

    def remove(self, obj):
        # obj = self.find(obj.get(name))
        typename = type(obj).__name__.lower()
        assert(obj in self[typename])
        index = self[typename].index(obj)
        return self[typename].pop(index)

    def keys(self):
        return [key for key in super(Element, self).keys() \
            if key.startswith(self.attribute_token)]

    def set(self, key, value):
        self.__setattr__(key, value)


    def tostring(self, pretty_print=True, indent=2, root='project'):
        #TODO This has to be rewritten...
        from dict2xml import dict2xml
        if not pretty_print: indent = 0
        return dict2xml(self, root, indent=indent, attribute_token=self.attribute_token)

    def tojson(self, indent=2):
        from json import dumps
        return dumps(self, indent=indent)

    def _attributes_to_string(self):
        attrib_keys = self.keys()
        attrib_str  = ['%s="%s"' % (k.strip(self.attribute_token), \
            str(self[k])) for k in attrib_keys]
        return ' '.join(attrib_str)

    def toxml(self, fileio, indent=0, whitespace=' '*4):
        """Turn element into XML tag locally.
        """
        has_children = '/' if self.keys() == super(Element, self).keys() else ''

        fileio.write('%s<%s %s%s>\n' % (whitespace*indent, self.tag,\
            self._attributes_to_string(), has_children))

        for child in self:
            if not child.text:
                child.toxml(fileio, indent=indent+1)
            else:
                fileio.write('%s<%s>\n' % (whitespace*(indent+1), child.tag))
                fileio.write('%s%s\n' % (whitespace*(indent+2), ' '.join(map(str, child.text))))
                fileio.write('%s<%s/>\n' % (whitespace*(indent+1), child.tag))

        if not has_children:
            fileio.write('%s</%s>\n' % (whitespace * indent, self.tag))
