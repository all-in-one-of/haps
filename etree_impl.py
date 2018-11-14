import collections, types
from collections import defaultdict

class HapsVal(collections.Sequence):
    data = []
    def __init__(self, values):
        super(HapsVal, self).__init__()
    def __getitem__(self, i):
        return self.data[i]
    def __len__(self):
        return len(self.data)
    def __repr__(self):
        return ' '.join(map(str, self.data))
    def __dict__(self):
        return {'value': str(self.data)}


    # pass
    # def __init__(self, data):
    #    self.data = list(data)

    # def next(self):
    #     if not self.data:
    #        raise StopIteration
    #     return self.data.pop()

    # def __iter__(self):
    #     return self
    # data = []
    # def __init__(self, *args):
    #     assert(args)
    #     for item in args:
    #         self.data.append(item)
    # def __iter__(self):
    #     for item in self.data:
    #         yield item
    # def __getitem__(self, idx):
    #     return self.data[idx]
    # def __len__(self):
    #     return len(self.data)


class Element(defaultdict):
    """Minimal implementation of xml.ElementTree API
       based on Python native dictionary.
    """
    attribute_token = 'attr:'

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
        super(Element, self).__setitem__(self.attribute_token+name, value)

    def __iter__(self):
        for typename, children in self.items():
            if typename.startswith(self.attribute_token):
                continue
            for child in children:
                yield child 

    def append(self, obj):
        """ Add child element to self. """
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
        """Extends element with collection of subelements."""
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
        """Find first child element of type name (tag)."""
        for typename, children in self.items():
            # only children, not attributes
            if not typename.startswith(self.attribute_token)\
                and typename == tag:
                return self[typename][0]
        return None

    def findall(self, tag):
        """Finds all children elements of a given type (tag)."""
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

    def __repr__(self):
        root=type(self).__name__.lower()
        return self.tostring(root=root)

    def tostring(self, pretty_print=True, indent=2, root='project'):
        #TODO This has to be rewritten...
        from dict2xml import dict2xml
        if not pretty_print: indent = 0
        return dict2xml(self, root, indent=indent, attribute_token=self.attribute_token)

    def tojson(self, indent=2):
        from json import dumps
        return dumps(self, indent=indent)