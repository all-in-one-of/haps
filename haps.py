
import collections, types
from collections import OrderedDict, defaultdict

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
        super(HapsObj, self).__setitem__('@'+name, value)

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
        return dict2xml(self, root, indent=indent)

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

class AssemblyInstance(HapsObj):
    pass

class Transform(HapsObj):
    pass

class Object(HapsObj):
    name = ''
    file = ''
    pass

class ObjectInstance(HapsObj):
    pass

class Color(HapsObj):
    pass

class Alpha(HapsVal):
    pass

class Parameter(HapsObj):
    value = ''
    pass

class Bsdf(HapsObj):
    pass

class Edf(HapsObj):
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


class Look_At(HapsObj):
    origin = (0,0,0)
    target = (0,0,0)
    up     = (0,0,0)


class Matrix(HapsVal):
    identity = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    def __init__(self, *args):
        super(Matrix, self).__init__(*args)
        if not args:
            super(Matrix, self).__init__(self.identity)


class Values(HapsVal):
    pass


def main():

    # Like this:
    object_  = Object(name='object', file='object.obj')
    assembly = Assembly(name='assembly')
    assembly.add(object_)

    obj_inst1 = ObjectInstance()
    obj_inst1.add(Transform().add(Matrix()))
    obj_inst2 = ObjectInstance()
    obj_inst2.add(Transform().add(Matrix()))
    assembly.add([obj_inst1, obj_inst2])

    # Or even this:
    assembly.add(Color(name='red').add(Alpha(1)).add(
                Parameter(name='color_space', value='sRGB')).add(
                    Values([0.1, 1, 2.0])
            )
        )

    assembly.add(Object(name='object2', file='filename2.obj'))

    scene    = Scene()
    scene.add(assembly)

    asmb_inst1 = AssemblyInstance().add(Transform().add(Matrix()))
    scene.add(asmb_inst1)

    scene.add(Camera(name="camera1", model="pinhole_camera").add(
        Transform().add(
            Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
        )
    )


    spectral = Color(name='green')
    spectral.add(Parameter(name='color_space', value='spectral'))
    spectral.add(Parameter(name='wavelength_range', value=[400, 700]))
    spectral.add(Values([0.092000, 0.097562, 0.095000, 0.096188, 0.097000]))
    spectral.add(Alpha([.5]))
    scene.add(spectral)


    scene.add(Bsdf(name='sphere_brdf', model='disney_brdf'))
    scene.add(Surface_Shader(name='sphere_shader', brdf='sphere_brdf'))
    scene.add(Material(name='greenish', surface_shader='sphere_shader'))

    project  = Project()
    project.add(scene)

    print project.tojson()
    print project









if __name__ == "__main__": main()