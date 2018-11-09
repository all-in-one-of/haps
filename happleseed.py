import haps
from happleseed_types import *


def Factory(typename,  name, parms=(), **kwargs):
    # FIXME: tuples in parm's values aren't collaped to strings (?)
    object_ = getattr(haps, typename)(name, **kwargs)
    assert isinstance(parms, collections.Iterable)
    for parm in parms:
        k, v = parm
        object_.add(haps.Parameter(k, v))
    return object_



class AppleSeed(object):
    project = None
    scene   = None
    assembly= None
    config  = None
    output  = None

    class TypeFactory(object):
        """ Lets try differnt approach.
        """
        def __init__(self, parent):
            self.parent = parent

        def add(self, typename, name, **kwargs):
            """Alias for insert()."""
            objects = self.create(typename, name, **kwargs)
            self.parent.add(objects)

        def insert(self, typename, name, **kwargs):
            """Inserts objects returned by create()."""
            objects = self.create(typename, name, **kwargs)
            self.parent.add(objects)


        def create(self, typename, name, **kwargs):
            """ Creates object of type 'typename' defined either
                inside this module or 'haps' module.
            """
            def _remove_duplicate(parent, obj):
                typename = type(obj).__name__.lower()
                if typename in parent.keys():
                    for elem in parent[typename]:
                        if elem[haps.attribute_token+'name'] == name:
                            index = parent[typename].index(elem)
                            return parent[typename].pop(index)
                return None

            from sys import modules

            thismodule = modules[__name__]
            if hasattr(thismodule, typename):
                objects = getattr(thismodule, typename)(name, **kwargs)
            elif hasattr(haps, typename):
                objects = (getattr(haps, typename)(name, **kwargs),)
            else:
                raise Exception("Can't create an object of unknow type: %s" % typename)
            for obj in objects:
                _remove_duplicate(self.parent, obj)
            return objects

    def __init__(self):
        """Creates bare minimum."""
        self.project = haps.Project()

    def Scene(self):
        """ Adds default scene object to a project and returns the object suitable
            for creation of entities to be added to the project on scene level.
        """
        if not self.scene: 
            self.scene = haps.Scene()
            self.project = haps.Project().add(self.scene)
        return self.TypeFactory(self.scene)

    def Assembly(self, name='assembly'):
        """ Returns the assembly 'name' from a scene object. In case it doesn't exist,
            return default one (self.assembly).
        """
        if not self.assembly:
            self.assembly = haps.Assembly('assembly')
            self.scene.add(self.assembly)
            self.scene.add(haps.Assembly_Instance(
                'default_asmb_inst', assembly=self.assembly))
        for assembly in self.scene['assembly']:
            if assembly[haps.attribute_token+'name'] == name:
                return self.TypeFactory(assembly)
        return self.TypeFactory(self.assembly)

    def Config(self, name=None, **kwargs):
        """Adds configuration object 'name' to the default configuration."""
        if not self.config:
            self.config = haps.Configurations()
            self.project.add(self.config)
        if not name: 
            return self.TypeFactory(self.config)
        for config in self.config['configuration']:
            if config[haps.attribute_token+'name'] == name:
                return  self.TypeFactory(config)
        return self.TypeFactory(self.config)

    def Output(self):
        """Adds Frame object to project.output."""
        if not self.output:
            self.output = haps.Output()
            self.project.add(self.output)
        return self.TypeFactory(self.output)

    def factory(self, parent='assembly'):
        assert(hasattr(self, parent))
        return self.TypeFactory(getattr(self, parent))



            








