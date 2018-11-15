from haps_types import HapsObj, HapsVal, FORMAT_REVISION


class Project(HapsObj):
    _children = []
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


class Frame(HapsObj):
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
    identity = (1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
    def __init__(self, m=None):
        if not m: m = self.identity
        assert(len(m) == 16)
        super(Matrix, self).__init__(m)

 