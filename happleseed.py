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


def SunLight(name, **kwargs):
    light = haps.Light(name, model='sun_light')
    light.add_parms([
            ("cast_indirect_light" , "true"),
            ("environment_edf" , "environment_edf"),
            ("importance_multiplier" , 1.0),
            ("radiance_multiplier" , 1.0),
            ("turbidity" , 1.0)
        ])
    light = update_parameters(light, **kwargs)
    edf, tmp = EnvironmentEdf('environment_edf')
    return light, edf #{'scene': [edf]}



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
    return env, {}



def Factory(typename,  name, parms=(), **kwargs):
    # FIXME: tuples in parm's values aren't collaped to strings (?)
    object_ = getattr(haps, typename)(name, **kwargs)
    assert isinstance(parms, collections.Iterable)
    for parm in parms:
        k, v = parm
        object_.add(haps.Parameter(k, v))
    return object_



class AppleSeed(object):
    def __init__(self):
        self.project = haps.Project()
        self.scene   = haps.Scene()
        self.project.add(self.scene)

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

        from sys import modules
        thismodule = modules[__name__]

        if hasattr(thismodule, typename):
            object_, objects = getattr(thismodule, typename)(name, **kwargs)
            _add_sideeffects(objects)
            self.scene.add(object_)
        elif hasattr(haps, typename):
            object_ = getattr(haps, typename)(name, **kwargs)
            self.scene.add(object_)

            








