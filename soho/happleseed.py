import haps
import happleseed_types
import collections
import types

import logging, sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def Factory(typename,  name, parms=(), **kwargs):
    # FIXME: tuples in parm's values aren't collaped to strings (?)
    object_ = getattr(haps, typename)(name, **kwargs)
    assert isinstance(parms, collections.Iterable)
    for parm in parms:
        k, v = parm
        object_.add(haps.Parameter(k, v))
    return object_


class AppleSeed(object):
    """ Our main class responsible for creating appleseed project.
        Should be smart enough to disallow user from creating
        misconstructed XML. Main responsibility of this class is
        constucting Factory object via funtions like Scene(), Assembly()
        (note capital character at front), which create and inserts haps 
        objects (atomics) and happleseed objects (compounds) likewise into
        a project. Nothing fancy exept it releases user from creating 
        everything by hand or making sure some elements are singelton
        and some other not.

        :example: 
                  apple = AppleSeed()
                  apple.Scene().insert(ThinLensCamera())
                  apple.Assembly().insert(MeshObject('box', filename='box.obj'))
                  apple.Assembly('second_assembly').insert(Light('lamp'))
    """
    # This probably should be initialized here, but then
    # we constraint the user from creating new scene in the project 
    # effectivelly starting from scratch (TODO rethink )
    # This means that whenever we want to use Factory, we
    # have to add default element (lots of waste of code, but potentialy
    # flexibility we need in some cases (like multithreading)).
    project  = None 
    scene    = None 
    assembly = None 
    config   = None 
    output   = None

    class TypeFactory(object):
        """ Lets try differnt approach.
        """
        def __init__(self, parent):
            self.parent = parent

        def add(self, typename, name, **kwargs):
            """Alias for insert()."""
            self.insert(typename, name, **kwargs)

        def insert(self, typename, name, **kwargs):
            """Call create() method and insert created objects into parent. 
            NOTE: we try to find and replace existing objects of type and name
            returned by create(). Should we make new method replace()?

            :parm typename: Object type to create. Both haps and happleseed types will do.
            :parm name:     Object name to create. 
            :parm kwargs:   optional kwargs passed to creation object.

            """
            objects = self.create(typename, name, **kwargs)
            self.emplace(objects)

        def emplace(self, objects, replace=True):
            """Insert pre-created objects into parent."""
            if not isinstance(objects, collections.Iterable):
                objects = [objects]
            if replace:
                for obj in objects:
                    duplicate =self.parent.get_by_name(obj.get('name', False))
                    if duplicate:
                        self.parent.remove(duplicate)
            self.parent.add(objects)

        def create(self, typename, name, **kwargs):
            """ Creates object of type 'typename' defined either
                inside this module or 'haps' module.
            """

            if hasattr(happleseed_types, typename):
                # logger.debug('from happleseed_types: %s', typename)
                objects = getattr(happleseed_types, typename)(name, **kwargs)
                if isinstance(objects, tuple):
                    objects = list(objects)
            elif hasattr(haps, typename):
                # logger.debug('from haps: %s', typename)
                objects = [getattr(haps, typename)(name, **kwargs)]
            else:
                raise Exception("Can't create an object of unknow type: %s" % typename)
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
        assembly = self.scene.get_by_name(name)
        if not assembly:
            assembly = haps.Assembly(name)
            instance = haps.Assembly_Instance(
                name+'_inst', assembly=assembly).add(
                haps.Transform().add(haps.Matrix()))
            self.scene.add([assembly, instance])

            if not self.assembly:
               self.assembly = assembly

        return self.TypeFactory(assembly)


    def Config(self, name=None, **kwargs):
        """Adds configuration object 'name' to the default configuration."""
        if not self.config:
            self.config = haps.Configurations()
            self.project.add(self.config)
        if not name: 
            return self.TypeFactory(self.config)
        
        config = self.config.get_by_name(name)
        if config:
                return  self.TypeFactory(config)

        else:
            raise Exception("Can't find a config %s" % name)

    def Output(self):
        """Adds Frame object to project.output."""
        if not self.output:
            self.output = haps.Output()
            self.project.add(self.output)
        return self.TypeFactory(self.output)

    def factory(self, parent='assembly'):
        assert(hasattr(self, parent))
        return self.TypeFactory(getattr(self, parent))



            











