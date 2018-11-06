
import collections, types
from collections import OrderedDict, defaultdict
attribute_token = '@'



class HapsVal(list):
    def __init__(self, *args):
        super(HapsVal, self).__init__(args)


class HapsObj(defaultdict):
    name = ''
    def __init__(self, **kwargs):
        """Init object with attribs from kwargs."""
        for k,v in kwargs.items():
            # Guards our object from setting unintended attributes:
            # assert(hasattr(self, k))
            # Collapses collec. of numbers to string:
            if isinstance(v, collections.Iterable) and \
            not isinstance(v, types.StringTypes):
                v = ' '.join(map(str, v))
            self.__setattr__(k, v)

    def __setattr__(self, name, value):
        """Maps Python object attribs to xml attribs via @notation in json."""
        # Guards our object from setting unintended attributes:
        #assert(hasattr(self, '@'+name))
        super(HapsObj, self).__setitem__(attribute_token+name, value)

    def add(self, obj):
        """ Add child or children to self. """
        def _add_value(v):
            typename = type(obj).__name__.lower()
            self[typename] = v

        if isinstance(obj, HapsVal):
            _add_value(obj)
            return self

        if isinstance(obj, list):
            [self.add(x) for x in obj if isinstance(x, HapsObj)]
            return self

        assert(isinstance(obj, HapsObj))
        typename = type(obj).__name__.lower()

        if typename in self: 
            self[typename] += [obj]
        else: 
            self[typename] = [obj]
        return self

    def __repr__(self):
        root=type(self).__name__.lower()
        return self.toxml(root=root)

    def toxml(self, root='project', indent=2):
        from dict2xml import dict2xml
        return dict2xml(self, root, indent=indent, attribute_token=attribute_token)

    def tojson(self, indent=2):
        from json import dumps
        return dumps(self, indent=indent)



class Project(HapsObj):
    pass


class Scene(HapsObj):
    pass


class Assembly(HapsObj):
    pass


class Camera(HapsObj):
    pass


class Assembly_Instance(HapsObj):
    pass


class Transform(HapsObj):
 
    pass

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
        self.__setattr__('name', name)
        if value:
            self.__setattr__('value', value)


class Bsdf(HapsObj):
    pass


class Edf(HapsObj):
    pass

class Environment(HapsObj):
    pass

class Environment_Shader(HapsObj):
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
    origin = (0,0,0)
    target = (0,0,0)
    up     = (0,0,0)


class Matrix(HapsVal):
    identity = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    def __init__(self, *args):
        if args:
            assert(len(args) == 16) 
            super(Matrix, self).__init__(*args)
        if not args:
            super(Matrix, self).__init__(self.identity)


class Values(HapsVal):
    pass


def ObjectFactory(hasp_object):
    pass


def dumps_schema():
    import json
    obj = Object(name='object', file='')
    schema = obj.tojson()
    with open('object.schema', 'w') as file:
        file.write(schema)



def main():
    # 
    project  = Project()
    scene    = Scene()
    assembly = Assembly(name='assembly')

    # Like this:
    object_  = Object(name='object', file='object.obj')
    assembly.add(object_)
    scene.add(assembly)

    # 
    obj_inst1 = Object_Instance(name='obj_inst1', object='object')
    obj_inst1.add(Transform().add(Matrix()))
    obj_inst2 = Object_Instance(name='obj_inst2', object='object')
    obj_inst2.add(Transform().add(Matrix(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)))
    assembly.add([obj_inst1, obj_inst2])

    # Assembly spageti add:
    assembly.add(Color(name='red').add(Alpha(1)).add(
                Parameter(name='color_space', value='sRGB')).add(
                    Values([0.1, 1, 2.0])
            )
        )
    assembly.add(Object(name='object2', file='filename2.obj'))

    #
    asmb_inst1 = Assembly_Instance().add(Transform().add(Matrix()))
    scene.add(asmb_inst1)

    # Camera:
    scene.add(Camera(name="camera1", model="pinhole_camera").add(
        Transform(time=0).add(
            Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
        )
    )

    # Colors:
    spectral = Color(name='green')
    spectral.add(Parameter('color_space', 'spectral'))
    spectral.add(Parameter('wavelength_range', [400, 700]))
    spectral.add(Values([0.092000, 0.097562, 0.095000, 0.096188, 0.097000]))
    spectral.add(Alpha([.5]))
    scene.add(spectral)

    # Materials:
    scene.add(Bsdf(name='sphere_brdf', model='disney_brdf'))
    scene.add(Surface_Shader(name='sphere_shader', brdf='sphere_brdf'))
    scene.add(Material(name='greenish', surface_shader='sphere_shader'))
    obj_inst1.add(Assign_Material(slot='Default', side='front', material='greenish'))



    frame = Frame(name='beauty').add(
        Parameter('camera', 'camera')).add(
        Parameter('resolution', '1024 1024')).add(
        Parameter('gamma_correction', "2.2"))

    project.add(Output().add(frame))
    project.add(scene)

    config = Configurations()
    config.add(Configuration(name='base_final').add(
        Parameter(name='frame_renderer', value='generic')).add(
        Parameter(name='tile_renderer', value='generic')).add(
        Parameter(name='pixel_renderer', value='uniform'))
    )
    config.add(Configuration(name='base_final').add(
        Parameter('frame_renderer', 'generic')).add(
        Parameter('tile_renderer',  'generic')).add(
        Parameter('pixel_renderer', 'uniform')).add(
        Parameter('light_engine', 'pt')).add(
        Parameter('pt').add(
            Parameter('dl_light_samples', 1)).add(
            Parameter('enable_ibl', "true"))
        )
    )
    project.add(config)



    print project.tojson()
    print project

    # dumps_schema()










if __name__ == "__main__": main()