import haps
import collections

def update_parameters(obj, **kwargs):
    token = haps.attribute_token
    keys = [parm[token+'name'] for parm in obj['parameter']]
    for key, value in kwargs.items():
        if key in keys:
            parm = obj['parameter'][keys.index(key)]
            parm[token+'value'] = value
    return obj
    

def ThinLensCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='thinlens_camera')
    camera.add_parms([
        ("shutter_open_time", 0.0),
        ("shutter_close_time",   1.0),
        ("film_dimensions", None), # FIXME:
        ("film_width", 1280), 
        ("film_height", 720),
        ("aspect_ratio", 1),
        ("focal_length", 40), 
        ("horizontal_fov", 45),
        ("f_stop",   8.0), 
        ("focal_distance",  1.0),
        ("autofocus_target",  [0.5, 0.5]),
        ("diaphragm_blades",  0),
        ("diaphragm_tilt_angle",  0.0),
        ("diaphragm_map",  ''),
        ("near_z",  -0.001)])
    camera = update_parameters(camera, **kwargs)
    return camera, None


def PinholeCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='pinhole_camera')
    camera.add_parms([
        ("shutter_open_time", 0.0),
        ("shutter_close_time",   1.0),
        ("film_dimensions", None),
        ("film_width", 1280), 
        ("film_height", 720),
        ("aspect_ratio", 1),
        ("focal_length", 40), 
        ("horizontal_fov", 45),
        ("near_z",  -0.001)])
    camera = update_parameters(camera, **kwargs)
    return camera, None

# TODO: make choices predefined (enumarator style)
# Possible values for filters are: blackman-harris (Blackman-Harris), box (Box), catmull (Catmull-Rom Spline), bspline (Cubic B-spline), gaussian (Gaussian), lanczos (Lanczos), mitchell (Mitchell-Netravali), triangle (Triangle).

def Frame(name, **kwargs):
    frame = haps.Frame(name)
    frame.add_parms([
        ("camera", None),
        ("resolution", [1280, 720]),  
        ("crop_window", None),
        ("tile_size" ,  16), 
        ("filter"  'blackman-harris'), 
        ("filter_size", 1.5 )])
    frame = update_parameters(frame, **kwargs)

    return frame, None


# def SunLight(name, **kwargs):
#     light = haps.Light(name, model='sun_light')
#     light.add_parms([
#             ("cast_indirect_light" , "true"),
#             ("environment_edf" , "environment_edf"),
#             ("importance_multiplier" , 1.0),
#             ("radiance_multiplier" , 1.0),
#             ("turbidity" , 1.0)
#         ])
#     light = update_parameters(light, **kwargs)
#     edf, tmp = EnvironmentEdf('environment_edf')
#     return light, edf #{'scene': [edf]}


def Environment(name, **kwargs):
    env = haps.Environment(name, model='generic_environment')
    env.add_parms([('environment_edf',   'environment_edf'),
                  ('environment_shader', 'environment_shader')])
    shader = haps.Environment_Shader('environment_shader',
        model='edf_environment_shader')
    shader.add(haps.Parameter('environment_edf', 'environment_edf'))
    edf = EnvironmentEdf('environment_edf', **kwargs)
    return env, shader, edf


def EnvironmentEdf(name, **kwargs):
    env = haps.Environment_Edf(name, model="preetham_environment_edf")
    env.add_parms([
            ("horizon_shift" ,"0.0" ),
            ("luminance_gamma" ,"1.0" ),
            ("luminance_multiplier" ,"1.0" ),
            ("saturation_multiplier" ,"1.0" ),
            ("sun_phi" ,"-15" ),
            ("sun_theta" ,"60" ),
            ("turbidity" ,"1.0" ),
            ("turbidity_multiplier" ,"1.0" ),
        ])
    env = update_parameters(env, **kwargs)
    return env, None


def SpectralColour(name, values=[1,1,1], alpha=1.0, **kwargs):
    colour = haps.Color(name)
    colour.add_parms([
        ('color_space', 'spectral'),
        ('wavelength_range', '400 700'),])
    colour.add(haps.Values(values).add(haps.Alpha([alpha])))
    colour = update_parameters(colour, **kwargs)
    return colour, None


def MeshObject(name, filename, **kwargs):
    object_ = haps.Object(name, model='mesh_object')
    object_.add(haps.Parameter('filename', filename))
    obj_inst = haps.Object_Instance('inst_'+name, object=name)
    obj_inst.add(haps.Transform().add(haps.Matrix()))
    return object_, obj_inst


def InteractiveConfiguration(name='base_interactive', **kwargs):
    conf = haps.Configuration(name, base='base_interactive')
    conf.add_parms([
            ("lighting_engine", "pt"),
            ("sampling_mode", "qmc")])
    conf.add(haps.Parameters('pt').add_parms([
                ("dl_light_samples", "1.000000"),
                ("dl_low_light_threshold", "0.000000"),
                ("enable_caustics", "true"),
                ("enable_dl", "true"),
                ("enable_ibl", "true"),
                ("ibl_env_samples", "1.000000"),
                ("max_bounces", "-1"),
                ("max_diffuse_bounces", "-1"),
                ("max_glossy_bounces", "-1"),
                ("max_specular_bounces", "-1"),
                ("next_event_estimation", "true"),
                ("rr_min_path_length", "6")]))
    return conf

def Factory(typename,  name, parms=(), **kwargs):
    # FIXME: tuples in parm's values aren't collaped to strings (?)
    object_ = getattr(haps, typename)(name, **kwargs)
    assert isinstance(parms, collections.Iterable)
    for parm in parms:
        k, v = parm
        object_.add(haps.Parameter(k, v))
    return object_



class AppleSeed(object):
    class TypeFactory(object):
        """ Lets try differnt approach.
        """
        def __init__(self, parent):
            self.parent = parent

        def create(self, typename, name, **kwargs):
            """
            """
            from sys import modules
            thismodule = modules[__name__]
            object_ = None
            if hasattr(thismodule, typename):
                objects = getattr(thismodule, typename)(name, **kwargs)
            elif hasattr(haps, typename):
                objects = getattr(haps, typename)(name, **kwargs)
            self.parent.add(objects)
            return objects

    def __init__(self):
        # This is helper infrastucture to build
        # minimal working environment
        self.project = haps.Project()
        self.scene   = haps.Scene()
        self.assembly= haps.Assembly('assembly') # this is just default one.
        self.scene.add(
            haps.Assembly_Instance(
                'default_asmb_inst', assembly='assembly'))
        self.output  = haps.Output().add(Frame('beauty'))
        self.config  = haps.Configurations()
        self.config.add(InteractiveConfiguration())

        self.scene.add(self.assembly)
        self.project.add(self.scene)
        self.project.add(self.output)
        self.project.add(self.config)

    def factory(self, parent='assembly'):
        assert(hasattr(self, parent))
        return self.TypeFactory(getattr(self, parent))

    def create(self, typename, name, **kwargs):
        '''Problem is obj can require existance of other object 
            they don't create themselfs. Should we bother?
            We could easily fix it with factory pattern where 
            new object is always created via parrent object.
            I'm not ready for that decision yet. 
        '''
        def _add_sideeffects(objects):
            # Allows Nones (???)
            if not objects: return
            assert(isinstance(objects, dict))
            for key in objects:
                if key == 'scene':
                    self.scene.add(objects[key])
                if key == 'project':
                    self.project.add(objects[key])
                if key == 'assembly':
                    self.scene['assembly'][0].add(objects[key])

        from sys import modules
        thismodule = modules[__name__]
        object_ = None

        if hasattr(thismodule, typename):
            objects = getattr(thismodule, typename)(name, **kwargs)
            _add_sideeffects(objects[1:])
            self.scene.add(objects[0])
        elif hasattr(haps, typename):
            objects = getattr(haps, typename)(name, **kwargs)
            self.scene.add(objects[0])

        return object_


            








