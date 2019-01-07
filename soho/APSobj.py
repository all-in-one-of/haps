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
        self.Assembly() # Just default one.
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


def update_parameters(obj, **kwargs):
    """Update object's parmaters with provided **kwargs.
    This is a helper function usually called by objects
    containing many parameters. TODO: we might move it into some object.

    :parm obj:      HapsObj to be updated
    :parm **kwargs: Python **kwargs arguments: name_of_parm=new_value
    :returns:       Modified object
    """
    for key, value in kwargs.items():
        parm = obj.get_by_name(key)
        # Ignore 
        if not parm:
            # logger.debug('Ignoring non existing parm: %s' % key)
            continue
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
        ("film_dimensions", '18.7 24.9'), # FIXME:
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
        ("shutter_open_time", '0.0'),
        ("shutter_close_time",   1.0),
        ("film_dimensions", '18.7 24.9'), # mm super35
        # ("aspect_ratio", 1),
        ("focal_length", 24), #mm
        ("horizontal_fov",   45),
        ("near_z",  -0.001)])
    camera = update_parameters(camera, **kwargs)
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

def MeshInstance(name, object, **kwargs):
    """Create mesh object and its instance with xform  applied.
    :parm name:     Name of the object
    :parm filename: Path to file object is saved in
    :parm kwargs:   dict of optional parameters: 
                    xform object (tuple of floats of length 16)
                    or xforms (series of xform object) suitable
                    for creating series of transformation blur.
    """

    obj_inst = haps.Object_Instance(name, object=object)

    # xforms
    xform = kwargs.get('xform') if kwargs.get('xform')\
        else haps.Matrix()
    if not kwargs.get('xforms'):
        obj_inst.add(haps.Transform().add(xform))
    else:
        obj_inst = TransformBlur(obj_inst, kwargs.get('xforms'))

    # materials:
    if not kwargs.get('materials'):
        slots     = ('default',)
        materials = ('default',)
    else:
        slots     = kwargs.get('slots')
        materials = kwargs.get('materials')

    assert(isinstance(slots,     collections.Iterable))
    assert(isinstance(materials, collections.Iterable))

    for slot, material in zip(slots, materials):
        obj_inst.add(haps.Assign_Material(None, 
            slot=slot, side='front', material=material))
        obj_inst.add(haps.Assign_Material(None, 
            slot=slot, side='back', material=material))

    return obj_inst


def MeshObject(name, filename, **kwargs):
    """Create mesh object and its instance with xform  applied.
    :parm name:     Name of the object
    :parm filename: Path to file object is saved in
    :parm kwargs:   dict of optional parameters: 
                    xform object (tuple of floats of length 16)
                    or xforms (series of xform object) suitable
                    for creating series of transformation blur.
    """
    obj = haps.Object(name, model='mesh_object')
    obj.add(haps.Parameter('filename', filename))
    #FIXME: is it general or only for obj without groups?
    obj_name = '.'.join([obj.get('name'), 'default']) 
    obj_inst = MeshInstance(name+"_inst", object=obj_name, **kwargs)

    return obj, obj_inst


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
            ("shading_result_framebuffer", "ephemeral")])

    conf.add(haps.Parameters('adaptive_pixel_renderer').add_parms([
        ('max_samples', 1),
        ('min_samples', 3),
        ('quality', 1.0)]))

    conf.add(haps.Parameters('uniform_pixel_renderer').add_parms([
        ('samples', 9),]))

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
    light = haps.Light(name, model='point_light')
    light.add_parms([
        ('cast_indirect_light', True),
        ('exposure', '0.0'),
        ('importance_multiplier', 1.0),
        ('intensity', 1.0),
        ('intensity_multiplier', 1.0)
        ])
    light = update_parameters(light, **kwargs)
    # xforms
    xform = kwargs.get('xform') if kwargs.get('xform')\
        else haps.Matrix()
    if not kwargs.get('xforms'):
        light.add(haps.Transform().add(xform))
    else:
        light = TransformBlur(light, kwargs.get('xforms'))
    return light


def Edf(name, model, **kwargs):
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
    """ Create gometry light. """
    cname = name+'/color'
    apscolor = Color(cname, values=color, alpha=1.0)

    edf = Edf(name + '_edf', model='diffuse_edf', 
        radiance=cname, exposure=exposure, radiance_multiplier=1)

    mat = haps.Material(name+ '_material', model='generic_material').add(
        haps.Parameter('edf', edf.get('name')))

    if not kwargs.get('xforms'): 
        xforms = [haps.Matrix()]
    else:
        xforms = [haps.Matrix(xform) for xform in kwargs.get('xforms')]

    materials = (mat.get('name'),)
    slots     = ('default',)
    absobjs = list(MeshObject(name, filename=filename, 
        xforms=xforms, materials=materials, slots=slots))
    absobjs[1].add(haps.Parameters("visibility").add_parms([
                ("camera", "false"),
                ("shadow", "false")]))
    absobjs += [edf, apscolor, mat]
    return absobjs

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





