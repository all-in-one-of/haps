import haps_types as haps
import collections
import types

def update_parameters(obj, **kwargs):
    """Update object's parmaters with provided **kwargs.
    This is a helper function usually called by objects
    containing many parameters. TODO: we might move it into some object.

    :parm obj:      HapsObj to be updated
    :parm **kwargs: usual Python kwargs arguments like: name_of_parm=new_value
    """
    for key, value in kwargs.items():
        parm = obj.get_by_name(key)
        if isinstance(value, collections.Iterable) and \
        not  isinstance(value, types.StringTypes):
            value = ' '.join(map(str, value))
        parm.set('value', value)
    return obj

def ThinLensCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='thinlens_camera')
    camera.add_parms([
        ("shutter_open_time", 0.0001),
        ("shutter_close_time",   1.0),
        ("film_dimensions", [0,0]), # FIXME:
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
    return camera


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
        ("resolution", "1280 720"),  
        ("crop_window", "0 0 1280 720"),
        ("tile_size" ,  "16 16"), 
        ("filter",  'blackman-harris'), 
        ("filter_size", 1.5 )])
    frame = update_parameters(frame, **kwargs)

    return frame, None

# Doesn't work, because of edf?
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
#     return light, edf 

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


def SpectralColor(name, values=[1,1,1], alpha=1.0, **kwargs):
    color = haps.Color(name)
    color.add_parms([
        ('color_space', 'spectral'),
        ('wavelength_range', '400 700'),])
    color.add(haps.Values(values).add(haps.Alpha([alpha])))
    color = update_parameters(color, **kwargs)
    return color, None


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
    return conf, None



def PhysicalSurfaceShader(name, lighting_samples=1):
    shader = haps.Surface_Shader(name, model='physical_surface_shader')
    shader.add(haps.Parameter('lighting_samples', lighting_samples))
    return shader, None

def DisneyMaterialLayer(name, layer_number, **kwargs):
    parms = haps.Parameters(name)
    parms.add_parms([
            ("anisotropic", "0"),
            ("base_color", "[0.619608, 0.309804, 0.164706]"),
            ("clearcoat", "0.0"),
            ("clearcoat_gloss", "1.0"),
            ("folded", "false"),
            ("layer_name", name),
            ("layer_number", layer_number),
            ("mask", "1"),
            ("metallic", "0.85"),
            ("roughness", "0.15"),
            ("sheen", "0.0"),
            ("sheen_tint", "0.0"),
            ("specular", "0.5"),
            ("specular_tint", "0.0"),
            ("subsurface", "0.0"),
        ])
    parms = update_parameters(parms, **kwargs)
    return parms, None

def DisneyMaterial(name, layers=1, **kwargs):
    shader   = PhysicalSurfaceShader('surface_shader')
    material = haps.Material(name, model='disney_material')
    material.add_parms([
                ("alpha_mask", "0"),
                ("bump_amplitude", "1.0"),
                ("displacement_method", "bump"),
                ("normal_map_up", "z"),
                ("surface_shader", "surface_shader")
        ])
    material = update_parameters(material, **kwargs)
    for layer in range(1, layers+1):
        name = 'layer%i' % layer
        material.add(DisneyMaterialLayer(name, layer))
    return shader, material
