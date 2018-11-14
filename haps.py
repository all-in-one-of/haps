
import collections, types
from collections import defaultdict
attribute_token = 'attr:'
FORMAT_REVISION = 27
from etree_impl import Element, HapsVal
# from xml.etree.ElementTree import Element, tostring



class HapsObj(Element):
   
    def __init__(self, name=None, **kwargs):
        """Init object with attribs from kwargs."""
        super(HapsObj, self).__init__(name, **kwargs)

    def add(self, obj):
        """"""
        #FIXME might want to remove it.
        if isinstance(obj, list) or isinstance(obj, tuple)\
            and type(obj) != HapsVal:
            print 'Many objects:' + str(obj)
            return self.extend(obj)
        else:
            return self.append(obj)

    def add_parms(self, parms):
        """Constructs & appends a parameters objects 
           from provided list of tuples suitable for parm's initalization.

           :parm parms: List of tuples [(str name, str value), (...,...)]
           :returns:    self
        """
        from haps_types import Parameter
        assert isinstance(parms, collections.Iterable)
        [self.append(Parameter(parm[0], parm[1])) for parm in parms\
             if len(parm) == 2 and isinstance(str,parm[0])]
        return self

    def get_by_type(self, typename):
        assert(typename in self.keys())
        return self[typename]

    def get_by_name(self, name, typename=None):
        """ Search for an item named 'name'.
            Optional 'typename' scopes the search. 
        """
        if typename:
            children = self.findall(typename)
            for child in children:
                if child.get('name') == name:
                    return child
        else: 
            for child in list(self):               
                if child.get('name') == name:
                    return child

        return None

    # def tostring(self):
    #     from xml.etree.ElementTree import tostring
    #     tostring(self)









