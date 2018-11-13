
import collections, types
from collections import defaultdict
attribute_token = 'attr:'
FORMAT_REVISION = 27


class HapsVal(list):
    def __init__(self, *args):
        assert(args)
        super(HapsVal, self).__init__(args)


class HapsObj(defaultdict):
    name = ''
    # TODO: Guard our object from setting unintended 
    # attributes: assert(hasattr(self, k))
    def __init__(self, name=None, **kwargs):
        """Init object with attribs from kwargs."""
        if name:
            self.__setattr__('name', name)
        for k,v in kwargs.items():
            # Turn Haps object into its name:
            if isinstance(v, HapsObj):
                v = v[attribute_token+'name']
            # Collapse iterrables to string:
            elif isinstance(v, collections.Iterable) and \
            not  isinstance(v, types.StringTypes):
                v = ' '.join(map(str, v))
            self.__setattr__(k, v)


    def __setattr__(self, name, value):
        """Maps Python object attribs to xml attribs via @notation in json."""
        super(HapsObj, self).__setitem__(attribute_token+name, value)


    def add(self, obj):
        """ Add child or children to self. """
        def _add_value(v):
            typename = type(obj).__name__.lower()
            self[typename] = v

        if isinstance(obj, HapsVal):
            _add_value(obj)
            return self

        if isinstance(obj, list) or isinstance(obj, tuple):
            [self.add(x) for x in obj]
            return self

        # We allow to pass Nones here:
        if obj == None: return self
        # ...but besides that only hapsies:
        assert(isinstance(obj, HapsObj))
        typename = type(obj).__name__.lower()

        if typename in self: 
            self[typename] += [obj]
        else: 
            self[typename] = [obj]
        return self

    def add_parms(self, parms):
        """Add parameters from a list of tuples sutable for parm's init.
        """
        assert isinstance(parms, collections.Iterable)
        [self.add(Parameter(parm[0], parm[1])) for parm in parms]
        return self

    def get(self, name):
        """"""
        attr = attribute_token+name
        if attr in self.keys():
            return self[attr]
        return None

    def find(self, name):
        return get_by_name(name)

    def get_by_name(self, name):
        """ Search for an item. """
        def get_child(children, name):
            attr = attribute_token+'name'
            for inst in children:
                    if attr in inst.keys():
                        if inst[attr] == name:
                            return inst
            return None

        for typename, children in self.items():
            # only children, not attributes
            if typename.startswith(attribute_token):
                continue
            result = get_child(children, name)
            if result:
                return result
    


        # We should not have two children of the same name:
        return None


    def __repr__(self):
        root=type(self).__name__.lower()
        return self.toxml(root=root)

    def toxml(self, root='project', indent=2):
        #TODO This has to be rewritten...
        from dict2xml import dict2xml
        return dict2xml(self, root, indent=indent, attribute_token=attribute_token)

    def tojson(self, indent=2):
        from json import dumps
        return dumps(self, indent=indent)



class Project(HapsObj):
    def __init__(self):
        self.__setattr__("format_revision", FORMAT_REVISION)


class Scene(HapsObj):
    pass


class Assembly(HapsObj):
    pass


class Camera(HapsObj):
    pass


class Assembly_Instance(HapsObj):
    pass


class Transform(HapsObj):
    def __init__(self, time=0):
        self.__setattr__('time', time)

class Object(HapsObj):
    pass


class Object_Instance(HapsObj):
    pass


class Color(HapsObj):
    pass


class Alpha(HapsVal):
    pass


class Parameter(HapsObj):
    def __init__(self, name, value=None):
        # super(Parameter, self).__init__(name, value=value)
        self.__setattr__('name', name)
        if value:
            self.__setattr__('value', value)

    # def __setattr__(self, name, value):
    #     if isinstance(value, collections.Iterable) and \
    #     not  isinstance(value, types.StringTypes):
    #         value = ' '.join(map(str, value))
    #     super(Parameter, self).__setattr__('@value', value)



class Parameters(HapsObj):
    def __init__(self, name):
        self.__setattr__('name', name)


class Bsdf(HapsObj):
    pass


class Edf(HapsObj):
    pass

class Environment(HapsObj):
    pass

class Environment_Shader(HapsObj):
    pass

class Environment_Edf(HapsObj):
    pass

class Light(HapsObj):
    pass


class Material(HapsObj):
    pass


class Assign_Material(HapsObj):
    pass


class Surface_Shader(HapsObj):
    pass


class Texture(HapsObj):
    pass


class Texture_Instance(HapsObj):
    pass


class Output(HapsObj):
    pass


class Frame(Object):
    pass


class Rules(HapsObj):
    pass


class Render_Layer_Assigment(HapsObj):
    pass 


class Configuration(HapsObj):
    pass


class Configurations(HapsObj):
    pass


class Look_At(HapsObj):
    pass


class Values(HapsVal):
    pass


class Matrix(HapsVal):
    identity = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    def __init__(self, *args):
        if args:
            assert(len(args) == 16) 
            super(Matrix, self).__init__(*args)
        if not args:
            super(Matrix, self).__init__(self.identity)






