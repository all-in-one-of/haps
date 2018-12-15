import haps
import collections

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
    camera = haps.update_parameters(camera, **kwargs)
    return camera


def PinholeCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='pinhole_camera')
    camera.add_parms([
        ("shutter_open_time", '0.0'),
        ("shutter_close_time",   1.0),
        ("film_dimensions", '1280 720'),
        ("aspect_ratio", 1),
        ("focal_length", 40), 
        ("horizontal_fov", 45),
        ("near_z",  -0.001)])
    camera = haps.update_parameters(camera, **kwargs)
    return camera

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
    frame = haps.update_parameters(frame, **kwargs)

    return frame

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
#     light = haps.update_parameters(light, **kwargs)
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
    env = haps.update_parameters(env, **kwargs)
    return env


def SpectralColor(name, values=[1,1,1], alpha=1.0, **kwargs):
    color = haps.Color(name)
    color.add_parms([
        ('color_space', 'spectral'),
        ('wavelength_range', '400 700'),])
    color.add(haps.Values(values).add(haps.Alpha([alpha])))
    color = haps.update_parameters(color, **kwargs)
    return color

def TransformBlur(obj, xforms):
    """Insert series of Transform object from provided matrices
    :parm obj:    Assembly, Object, Light, etc
    :parm xform:  List of Matrix obj.
    :returns:     modified obj

    """
    timestep = 1.0 / len(xforms)
    assert(isinstance(xforms, collections.Iterable))
    for idx in range(len(xforms)):
        assert(isinstance(xforms[idx], haps.Matrix))
        obj.add(haps.Transform(time=timestep*idx).add(xforms[idx]))
    return obj

def MeshObject(name, filename, **kwargs):
    """Create mesh object adn its instance with transformation applied.
    """
    xform = kwargs.get('xform') if kwargs.get('xform')\
        else haps.Matrix()
    object_ = haps.Object(name, model='mesh_object')
    object_.add(haps.Parameter('filename', filename))
    obj_name = '.'.join([object_.get('name'), object_.get('name')])
    obj_inst = haps.Object_Instance(name+'_inst', object=object_.get('name')+".group1")
    if not kwargs.get('xforms'):
        obj_inst.add(haps.Transform().add(xform))
    else:
        obj_inst = TransformBlur(obj_inst, kwargs.get('xforms'))
    return object_, obj_inst


def InteractiveConfiguration(name='interactive', **kwargs):
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


def FinalConfiguration(name='final', **kwargs):
    conf = haps.Configuration(name, base='base_final')
    conf.add_parms([
            ("lighting_engine", "pt"),
            ("passes", "1"),
            ("pixel_renderer", "uniform"),
            ("sampling_mode", "qmc"),
            ("shading_result_framebuffer", "ephemeral")])

    conf.add(haps.Parameters('adaptive_pixel_renderer').add_parms([
        ('max_samples', 256),
        ('min_samples', 16),
        ('quality', 2.0)]))

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

def PhysicalSurfaceShader(name, lighting_samples=1):
    shader = haps.Surface_Shader(name, model='physical_surface_shader')
    shader.add(haps.Parameter('lighting_samples', lighting_samples))
    return shader


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
    parms = haps.update_parameters(parms, **kwargs)
    return parms


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
    material = haps.update_parameters(material, **kwargs)
    for layer in range(1, layers+1):
        name = 'layer%i' % layer
        material.add(DisneyMaterialLayer(name, layer, **kwargs))
    return shader, material

