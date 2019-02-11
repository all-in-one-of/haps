import collections
import types
import inspect 
import haps

def Factory(typename,  name, parms=(), **kwargs):
    # This is depracated.
    object_ = getattr(inspect.getmodule(haps), typename)(name, **kwargs)
    assert isinstance(parms, collections.Iterable)
    for parm in parms:
        k, v = parm
        object_.add(haps.Parameter(k, v))
    return object_


class Appleseed(object):
    """ 
        :example: 
                  apple = Appleseed()
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
            current_module = inspect.getmodule(self)
            if hasattr(current_module, typename):
                objects = getattr(current_module, typename)(name, **kwargs)
                if isinstance(objects, tuple):
                    objects = list(objects)
            elif hasattr(haps, typename):
                objects = [getattr(haps, typename)(name, **kwargs)]
            else:
                raise Exception("Can't create an object of unknow type: %s" % typename)
            return objects

    def __init__(self):
        """Creates bare minimum."""
        self.project = haps.Project()
        self.Scene() 
        # self.Assembly() # Just default one.
        # self.Config()
        # self.Output()

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


def update_parameters_no_req(obj, **kwargs):
    """Update object's parmaters with provided **kwargs.
    This is a helper function usually called by objects
    containing many parameters.
    (TODO: to be removed as recursive version
    prove its strength.)

    :parm obj:      HapsObj to be updated
    :parm **kwargs: Python **kwargs arguments: name_of_parm=new_value
    :returns:       Modified object
    """
    for key, value in kwargs.items():
        parm = obj.get_by_name(key)
        if not parm:
            continue
        if isinstance(value, collections.Iterable) and \
        not  isinstance(value, types.StringTypes):
            value = ' '.join(map(str, value))
        parm.set('value', value)
    return obj


def update_parameters(obj, **kwargs):
    """Update object's parmaters with provided **kwargs.
    This is a helper function usually called by objects
    containing many parameters. This function supports 
    update using /path/entitiy notation (recursive).

    NOTE: that we do not add parms to the object here.
    None existing parms are simply ignored.
    (We could actually support it, but this quickly
        would become a mess.)

    :parm obj:      HapsObj to be updated

    :parm **kwargs: Python **kwargs arguments: name_of_parm=new_value
    :returns      : Modified object
    """
    def extract_root_from_path(path, denominator='/'):
        # can I use posixpath here?
        tree = path.split(denominator)
        if len(tree) == 1: 
            return tree, []
        else: 
            return tree[0], denominator.join(tree[1:])

    for key, value in kwargs.items():
        parm = obj.get_by_name(key)
        # No match here 
        if not parm: 
            parent, children = extract_root_from_path(key)
            parm = obj.get_by_name(parent)
            # and not bellow
            if not parm:
                continue
            # send request deeper
            children_kwargs = {children: value}
            update_parameters(parm, **children_kwargs)
        else:
            # else do as usual
            if isinstance(value, collections.Iterable) and \
            not  isinstance(value, types.StringTypes):
                value = ' '.join(map(str, value))
            parm.set('value', value)

    return obj
    
            
def ThinLensCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='thinlens_camera')
    camera.add_parms([
        ("autofocus_enabled", "false"),
        ("autofocus_target", "0.5 0.5"),
        ("diaphragm_blades", "6"),
        ("diaphragm_map", ""),
        ("diaphragm_tilt_angle", '0.0'),
        ("f_stop", '8.0'),
        ("film_dimensions", "0.01024 0.00576"),
        ("focal_distance", '1.0'),
        ("horizontal_fov", "38.505"),
        ("near_z", "-0.001"),
        ("shift_x", "0.0"),
        ("shift_y", "0.0"),
        ("shutter_open_begin_time", '0.0'),
        ("shutter_open_end_time", '0.0'),
        ("shutter_close_begin_time", '0.0'),
        ("shutter_close_end_time", '0.0'),
        ])
    camera = update_parameters(camera, **kwargs)

    xforms = kwargs.get('xforms')
    times  = kwargs.get('times')
    if not xforms:
        xforms = [haps.Matrix.identity]
        times  = [0.0]
    camera = TransformBlur(camera, xforms, times)
    
    return camera


def PinholeCamera(name, **kwargs):
    camera = haps.Camera(name=name, model='pinhole_camera')
    camera.add_parms([
        ("shutter_close_begin_time", '0.0'),
        ("shutter_close_end_time", '0.0'),
        ("shutter_open_begin_time", '0.0'),
        ("shutter_open_end_time", '0.0'),
        ("film_dimensions", '18.7 24.9'), # mm super35
        ("horizontal_fov",   45),
        ("near_z",  -0.001)])
    camera = update_parameters(camera, **kwargs)

    xforms = kwargs.get('xforms')
    times  = kwargs.get('times')
    if not xforms:
        xforms = [haps.Matrix.identity]
        times  = [0.0]
    camera = TransformBlur(camera, xforms, times)

    return camera

# TODO: make choices predefined (enumarator style)
# Possible values for filters are: blackman-harris (Blackman-Harris), 
# box (Box), catmull (Catmull-Rom Spline), bspline (Cubic B-spline), 
# gaussian (Gaussian), lanczos (Lanczos), mitchell (Mitchell-Netravali), triangle (Triangle).

def Frame(name, **kwargs):
    frame = haps.Frame(name)
    frame.add_parms([
        ("camera", None),
        ("resolution", "1280 720"),  
        ("crop_window", "0 0 1280 720"),
        ("tile_size" ,  "64 64"), 
        ("filter",  'gaussian'), 
        ("filter_size", 1.5 )])
    frame = update_parameters(frame, **kwargs)

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
    return env


def SpectralColor(name, values=[1,1,1], alpha=1.0, **kwargs):
    color = haps.Color(name)
    color.add_parms([
        ('color_space', 'spectral'),
        ('wavelength_range', '400 700'),])
    color.add(haps.Values(values).add(haps.Alpha([alpha])))
    color = update_parameters(color, **kwargs)
    return color


def Color(name, values=[1,1,1], alpha=1.0, **kwargs):
    color = haps.Color(name)
    color.add_parms([
        ('color_space', 'linear_rgb'),
        ('multiplier', '1.0'),])
    color.add(haps.Values(values)).add(haps.Alpha([alpha]))
    color = update_parameters(color, **kwargs)
    return color
    

def TransformBlur(obj, xforms, times=[]):
    """Insert series of Transform object from provided matrices
    :parm obj:    Assembly, Object, Light, etc
    :parm xform:  List of Matrix obj.
    :returns:     modified obj

    """
    assert(isinstance(xforms, collections.Iterable))

    if not times:
        for step in range(len(xforms)):
            times += [1.0/step]

    assert(len(xforms) == len(times))

    for time, xform in zip(times, xforms):
        assert(isinstance(xform, collections.Iterable))
        assert(len(xform) == 16)
        assert(isinstance(time, float))
        obj.add(haps.Transform(time=time).add(haps.Matrix(xform)))

    return obj

def MeshInstance(name, object, **kwargs):
    """Create mesh instance with xform  applied.
    :parm name     : Name of the object we are instance of
    :parm materials: List of materials we will assign
    :parm slots    : List of slots we will assign to
    :parm xforms   : list of tuples/lists with 4x4 floats (can be None)
    :parm times    : list of times samples for xforms    (can be None)
    :parm kwargs   : additional args          
    """
    obj_inst = haps.Object_Instance(name, object=object)

    # This is ugly, but I don't know how to add only stuff
    # which is not at default state now.
    if True in [key.startswith('visibility') for key in kwargs]:
        obj_inst.add(haps.Parameters('visibility').add_parms([
            ('shadow',   'true'),
            ('camera',   'true'),
            ('specular', 'true'),
            ('glossy' ,  'true'),
            ]))

    obj_inst = update_parameters(obj_inst, **kwargs)

    xforms    = kwargs.get('xforms') # [] is correct
    times     = kwargs.get('times')
    materials = kwargs.get('materials')
    slots     = kwargs.get('slots')

    if not materials:
        materials = ('default',)

    if not slots:
        slots = ('default',)

    if xforms and not times:
        times = [time*1.0/len(xforms) for time in range(len(xforms))]

    if xforms and times:
        obj_inst = TransformBlur(obj_inst, xforms, times)

    assert(isinstance(slots,     collections.Iterable))
    assert(isinstance(materials, collections.Iterable))

    for slot, material in zip(slots, materials):
        obj_inst.add(haps.Assign_Material(None, 
            slot=slot, side='front', material=material))
        obj_inst.add(haps.Assign_Material(None, 
            slot=slot, side='back', material=material))

    return obj_inst


def MeshObject(name, filename, **kwargs):
    """Create mesh object and its instance with xform applied.
    :parm name:     Name of the object
    :parm filename: Path to file object is saved in
    :parm kwargs:   dict of optional parameters: 
                    xform object (tuple of floats of length 16)
                    or xforms (series of xform object) suitable
                    for creating series of transformation blur.
    """

    obj = haps.Object(name, model='mesh_object')
    obj.add(haps.Parameter('filename', filename))
    obj_name = '.'.join([obj.get('name'), 'default']) 


    obj_inst = MeshInstance(name+"_inst", object=obj_name,  **kwargs)

    return obj, obj_inst


def AssemblyInstance(name, assembly, **kwargs):
    '''An instance of the assembly. Has own trasform and visibility flags.
    '''
    assembly_inst = haps.Assembly_Instance(name, assembly=assembly)
    if True in [key.startswith('visibility') for key in kwargs]:
        assembly_inst.add(haps.Parameters('visibility').add_parms([
            ('shadow',   'true'),
            ('camera',   'true'),
            ]))
    xforms = kwargs.get('xforms') # [] is correct
    times  = kwargs.get('times')
    
    if xforms and times:
        assembly_inst = TransformBlur(assembly_inst, xforms, times)

    assembly_inst = update_parameters(assembly_inst, **kwargs)

    return assembly_inst

def AssemblyObject(name, filenames, list_of_kwargs, **kwargs):
    """Creates an assembly from one or multiply objects.
       all kwargs becomes tuples of kwargs.
    """
    members = []
    for filename, _kwargs in zip(filenames, list_of_kwargs):
        # print filename
        # print _kwargs
        members += MeshObject(name, filename, **_kwargs)

    assembly = haps.Assembly(name)
    assembly.add(members)

    inst   = AssemblyInstance(name+"_inst", name,  **kwargs)
    return assembly, inst


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
                ("max_bounces", "4"),
                ("max_diffuse_bounces", "4"),
                ("max_glossy_bounces", "4"),
                ("max_specular_bounces", "4"),
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
            ("shading_result_framebuffer", "ephemeral"),
            ('spectrum_mode', 'rgb'),
            ('rendering_threads', '0') 
            ])

    conf.add(haps.Parameters('light_sampler').add_parms([
        ('algorithm', 'cdf')
        ]))

    conf.add(haps.Parameters('uniform_pixel_renderer').add_parms([
        ('samples', 9),
        ('decorrelate_pixels', 'true'),
        ('force_antialiasing', 'true')
        ]))

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
                ("rr_min_path_length", "6")
                ]))

    conf.add(haps.Parameters('sppm').add_parms([                 
                ("alpha", "0.700000"),
                ("dl_mode", "rt"),
                ("enable_caustics", "true"),
                ("enable_ibl", "true"),
                ("env_photons_per_pass", "1000000"),
                ("initial_radius", "0.100000"),
                ("light_photons_per_pass", "1000000"),
                ("max_photons_per_estimate", "100"),
                ("path_tracing_max_bounces", "-1"),
                ("path_tracing_rr_min_path_length", "6"),
                ("photon_tracing_max_bounces", "-1"),
                ("photon_tracing_rr_min_path_length", "6"),
                ("photon_type", "poly"),
                ]))


    return conf

def PhysicalSurfaceShader(name, lighting_samples=1):
    shader = haps.Surface_Shader(name, model='physical_surface_shader')
    shader.add(haps.Parameter('lighting_samples', lighting_samples))
    return shader


def DefaultLambertMaterial(name, color=[.5,.5,.5]):
    ''''''
    rgb = haps.Color(name+'_color')
    rgb.add_parms([
        ('multiplier', 1.0),
        ('wavelength_range', '400.0 700.0'),
        ('color_space', 'linear_rgb')])

    rgb.add(haps.Values(color))
    rgb.add(haps.Alpha([1.0]))

    bsdf = haps.Bsdf(name+'_bsdf', 
        model='lambertian_brdf').add_parms([
        ('reflectance', rgb.get('name'))])

    shader   = PhysicalSurfaceShader(name+"_shader", lighting_samples=1)
    material = haps.Material(name, model='generic_material')
    material.add_parms([
            ('bsdf', bsdf.get('name')),
            ('surface_shader', shader.get('name'))])
    return rgb, bsdf, shader, material


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
    return parms


def DisneyMaterial(name, layers=1, **kwargs):
    shader   = PhysicalSurfaceShader('surface_shader')
    material = haps.Material(name, model='disney_material')
    material.add_parms([
                ("surface_shader", "surface_shader"),
                ('edf', None),
                ("alpha_map", "0"),
                ("bump_amplitude", "1.0"),
                ("displacement_method", "bump"),
                ("normal_map_up", "z"),
        ])
    material = update_parameters(material, **kwargs)
    for layer in range(1, layers+1):
        name = 'layer%i' % layer
        material.add(DisneyMaterialLayer(name, layer, **kwargs))
    return shader, material


def PointLight(name, **kwargs):
    '''Non-physical point light'''
    light = haps.Light(name, model='point_light')
    light.add_parms([
        ('cast_indirect_light', True),
        ('exposure', '0.0'),
        ('importance_multiplier', 1.0),
        ('intensity', 1.0),
        ('intensity_multiplier', 1.0)
        ])

    light  = update_parameters(light, **kwargs)
    return light


def Edf(name, model, **kwargs):
    '''Edf mostly for geometry lights.'''
    edf = haps.Edf(name, model=model)
    edf.add_parms([
        ("cast_indirect_light", True),
        ("importance_multiplier", 1.0),
        ("light_near_start", "0.0"),
        ("radiance", 1.0),
        ("radiance_multiplier", 1.0),
        ("exposure", 0)
    ])
    edf = update_parameters(edf, **kwargs)
    return edf


def MeshLight(name, filename, color=(1,1,1), exposure=0, **kwargs):
    """ Geometry light is normals meshe with Edf applied
    on its material.
    """
    color_name = name+'/color'
    color_obj  = Color(color_name, values=color, alpha=1.0)

    edf = Edf(name + '_edf', model='diffuse_edf', 
        radiance=color_name, exposure=exposure, radiance_multiplier=1)

    material = haps.Material(name+ '_material', model='generic_material').add(
        haps.Parameter('edf', edf.get('name')))

    materials = (material.get('name'),)
    slots     = ('default',)

    kwargs['visibility/camera'] = 'false'
    kwargs['visibility/shadow'] = 'false'

    light_objs = list(MeshObject(name, filename=filename, materials=materials, 
        slots=slots,  **kwargs))
   
    light_objs += [edf, color_obj , material]
    return light_objs


def DiskTexture2D(name, filename, **kwargs):
    texture = haps.Texture(name, model='disk_texture_2d').add_parms([
        ("color_space", "srgb"),# FIXME make auto switcher
        ("filename", filename)])
    texture = update_parameters(texture, **kwargs)
    texture_instance = haps.Texture_Instance(name+'_inst', texture=name).add_parms([
        ("addressing_mode", "clamp"),
        ("filtering_mode", "nearest"),])
    texture_instance = update_parameters(texture_instance, **kwargs)
    return texture, texture_instance





