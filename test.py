from haps import *

""" 
    Experiments with API design for Appleseed for Houdini.
"""

def main():

    # Low level haps.py interface:
    # Main parts project, scene, assembly
    # HapsObj1.add(HapsObj2):
    #       -> adds HapsObj2 into HapsObj1 as xml child node:
    project  = Project()
    scene    = Scene()
    assembly = Assembly('assembly')
    scene.add(assembly)

    # Initial arguments are always xml attributes:
    # First argument is always a name
    object1  = Object(name='mesh1', file='mesh1.obj')
    # ...so we can drop it
    object2  = Object('mesh2', file='mesh2.obj')

    # We can add lists of objecs...
    assembly.add([object1, object2]) 

    # Instances of objects NOTE: we can reference objects 
    # (as opposed to their names) in args, albeit it's buggy atm
    obj_inst1 = Object_Instance('obj_inst1', object='mesh1')
    obj_inst2 = Object_Instance('obj_inst2', object=object1)
    # Default transform with ident matrix at time 0.0:
    obj_inst1.add(Transform().add(Matrix()))
    # or mock something else  (at time .5)
    obj_inst2.add(Transform(.5).add(Matrix(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)))

    assembly.add([obj_inst1, obj_inst2])

    # Assembly spaggeti addition (ugly but handy)
    assembly.add(Color('red').add(Alpha(1)).add(
                Parameter('color_space', 'sRGB')).add(
                    Values([0.1, 1, 2.0])))

    # Assemblies also seem to be instanceable
    asmb_inst1 = Assembly_Instance('asm1', assembly=assembly).add(Transform().add(Matrix()))
    scene.add(asmb_inst1)

    # Row camera:
    scene.add(Camera("camera1", model="pinhole_camera").add(
        Transform(time=0).add(
            Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
        )
    )

    # Row Colours:
    spectral = Color('green')
    spectral.add(Parameter('color_space', 'spectral'))
    spectral.add(Parameter('wavelength_range', [400, 700]))
    spectral.add(Values([0.092000, 0.097562, 0.095000, 0.096188, 0.097000]))
    spectral.add(Alpha([.5]))
    scene.add(spectral)

    # Materials + assigment:
    bsdf = Bsdf('sphere_brdf', model='disney_brdf')
    scene.add(bsdf)
    scene.add(Surface_Shader('sphere_shader', brdf=bsdf))
    scene.add(Material('greenish', surface_shader='sphere_shader'))
    obj_inst1.add(Assign_Material(slot='Default', side='front', material='greenish'))

    # Env + env_shader + Edf
    scene.add(Environment('env', environment_shader='env_shader')).add(
        Environment_Shader('env_shader', edf='edf')).add(Edf('edf', model='cone_edf'))
    project.add(scene)

    # Frame
    frame = Frame('beauty').add(
        Parameter('camera', 'camera')).add(
        Parameter('resolution', '1024 1024')).add(
        Parameter('gamma_correction', "2.2"))

    # is a part of output section:
    project.add(Output().add(frame))

    # There is config and number of configs inside:
    # Also we could get rid of Parameters (as some
    # types have so many of them) with HapsObj.add_parms([...])
    config = Configurations()
    config.add(Configuration('base_interactive').add_parms([
        ('frame_renderer', 'generic'), 
        ('tile_renderer', 'generic'),
        ('pixel_renderer', 'uniform')]))


    # Even more nested nodes:
    config.add(Configuration('base_final').add([
        Parameter('frame_renderer', 'generic'),
        Parameter('tile_renderer',  'generic'),
        Parameter('pixel_renderer', 'uniform'),
        Parameter('light_engine', 'pt').add(
            Parameters('pt').add([
                Parameter('dl_light_samples', 1), 
                Parameter('enable_ibl', "true")])
            )
        ])
    )

    #
    project.add(config)
    # We're done:
    # print project
    xml = project.toxml()
    # with open(filename, 'w') as file: file.write(xml) etc...


    # Higher level interface (happleseed.py)
    # TODO: delegate candidates for higher life existance: 
    # cameras, lights, configs, spectral colors?
    import happleseed
    project = Project()
    scene   = Scene()

    # (1) happleseend.Callable() returns HapsObj
    # type + dict with additional objects created by the type 
    # in order to be complete. They have to be added to project or scene 
    # (like bsdfs, edfs, shaders etc)
    # This becomes ugly...
    camera, something_we_dont_know = happleseed.ThinLensCamera('renderCam')
    # something_we_dont_know has to be added manually either to project or scene 
    # or gods know where else?
    scene.add(camera)

    # (2) maybe with explicite factory (does it bring much to the table?)
    scene = Scene()
    scene.add(happleseed.Factory('Frame','beauty', 
        parms=(('resolution' ,[1920, 1080]),), 
        camera='renderCam2'))
    scene.add(happleseed.Factory('Camera', 'renderCam2', 
        parms=(('aspect_ratio',1), ), model="pinhole_camera"))
    # print scene

    # (3) or more object oriented?
    # (1), (2) and (3) could and perhpas should be used together:
    # We take care of complete creation by ourselfs:
    apple = happleseed.AppleSeed()
    apple.scene = Scene()
    apple.scene.add(happleseed.ThinLensCamera('renderCam'))
    apple.scene.add(happleseed.Factory('Frame','beauty', 
        parms=(('resolution' ,[1920, 1080]),), 
        camera='renderCam'))

    # we don't bother
    apple.project.add(Configurations().add(Configuration("final").add_parms([
        ('frame_renderer', 'generic'), 
        ('tile_renderer', 'generic'),
        ('pixel_renderer', 'uniform')])))
    
    # Some mixed ideas
    # point light is added directly to assembly
    apple.assembly = Assembly('assembly')
    apple.assembly.add(Light('point_light').add(Transform().add(Matrix())))
    # assembly to scene likewise
    apple.scene.add(Assembly('assembly2'))
    #
    apple.scene['assembly'][0].add(Light('point_light'))
    #
    assembly = apple.scene['assembly'][0] # get default one
    #
    # How about create context with parent, is it general? Probably not.
    apple = happleseed.AppleSeed()  
    apple.scene = Scene()
    apple.assembly = Assembly('assembly')
    apple.project.add(apple.scene)
    apple.scene.add(apple.assembly)  
    # by default first assembly is a scene:
    apple.factory().create('Light', 'lamp', model='point_light')
    # This addes three objects:
    apple.factory('scene').create('Environment', 'preetham_env', turbidity=2.0)
    # len(objects) == 3
    objects = happleseed.Environment('preetham_env', turbidity=2.0) 
    # This for example is not valided with Appleseed schema: 
    # apple.factory('scene').create('MeshObject'))
    mesh = apple.factory().create('MeshObject','mesh1', filename="mesh.obj")

    # Yet another way
    apple = happleseed.AppleSeed()
    apple.Scene().add('Environment', 'preetham_env', turbidity=2.0)
    apple.Assembly('assembly').add('Light', 'sun', model='point_light')
    apple.Assembly().add('MeshObject', 'torus', filename='torus.obj')
    apple.scene.add(Assembly('new_assembly'))
    apple.scene.add(Assembly_Instance('na_inst', assembly='new_assembly'))
    apple.Assembly('new_assembly').add('MeshObject', 'torus', filename='torus.obj')
    apple.Config().insert('InteractiveConfiguration', 'base_interactive')
    # Replace one element:
    apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='pt')
    apple.Output().insert('Frame', 'beauty', resolution=[1920, 1080])
    apple.Assembly().insert('DisneyMaterial', 'some_disney_material', base_color=[1,0,0])


    # Debug with line number
    counter = 1
    for line in str(apple.project).split('\n'):
        print str(counter) + "   " + line
        counter += 1


    c = apple.config.get_by_name('base_interactive')
    print c.get_by_name('pt').get_by_name('max_bounces').get('value')


    # Higher level should take care of a placement policy (xml schema)
    # to be really useful. How to make it happen? 
    # Callable()s could specifily their details with attributes? 
    # Also should Python object contain its schema or should be deduced 
    # from json/xml (I usually like this approach)?

    # Play with validation:
    try:
        import lxml
    except:
        print "No lxml module. Quiting now."
        quit()

    from lxml import etree
    schema_path = "../appleseed/sandbox/schemas/project.xsd"
    xml = etree.XML(apple.project.toxml())
    xmlschema_doc = etree.parse(schema_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    xmlschema.assertValid(xml)



if __name__ == "__main__": main()
