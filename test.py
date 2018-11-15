from haps_types import *
from haps import FORMAT_REVISION

""" 
    Experiments with API design for Appleseed for Houdini.
"""

def splitXMLtoWords(xml, whitespace='\n'):
    return [word.strip() for word in \
        str(xml).split(whitespace) if word != ""]

def main():

    minimal_project = ['<project format_revision="%i">' % FORMAT_REVISION, '<scene>', 
        '<assembly name="assembly"/>', '</scene>', '</project>']

    # Low level haps.py interface:
    project  = Project()
    scene    = Scene()
    assembly = Assembly('assembly')
    scene.add(assembly)
    project.add(scene)
    assert(splitXMLtoWords(str(project)) == minimal_project)

    # __init__ arguments are always XML attributes, first argument is always a name:
    object1  = Object(name='torus', model='mesh_object').add(Parameter('filename', 'torus.obj'))
    # ...so we can drop it:
    object2  = Object('torus', model='mesh_object').add(Parameter('filename', 'torus.obj'))

    assert(str(object1) == str(object2))

    # Add objects, its instance and defaulf transform:
    object1    = Object('box', model='mesh_object').add_parms([('filename', 'box.obj')])
    obj1_inst1 = Object_Instance('inst_'+'torus', object='box').add(Transform().add(Matrix()))
    assembly.add([object1, obj1_inst1])

    assert(assembly.find('object') and assembly.find('object_instance'))
    assert(assembly.get_by_name('box') and assembly.get_by_name('inst_torus'))

    # Transforms have broken xml encoder which works corrently only in recursive case (above not bellow)
    ident = (1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
    assert(str(Transform().add(Matrix())) == str(Transform().add(Matrix(ident))))


    # Instances of objects NOTE: we can reference objects 
    # (as opposed to their names) in arguments
    obj_inst1 = Object_Instance('obj_inst1', object='box')
    obj_inst2 = Object_Instance('obj_inst1', object=object1)
    assert(str(obj_inst1) == str(obj_inst2))


    # Assembly spaggeti addition (ugly but handy)
    assembly.add(Color('red').add(Alpha([1])).add(
                Parameter('color_space', 'sRGB')).add(
                    Values([0.1, 1, 2.0])))

    assert(assembly.find('color').get('name') == 'red')
    assert(str(assembly.find('color').find('alpha')) == '1')
    assert(assembly.find('color').find('values').data == [0.1, 1, 2.0])

    # Assemblies also seem to be instanceable
    asmb_inst1 = Assembly_Instance('asm1', assembly=assembly).add(Transform().add(Matrix()))
    scene.add(asmb_inst1)
    assert(scene.find('assembly_instance'))


    # Row camera:
    scene.add(Camera("camera1", model="pinhole_camera").add(
        Transform(time=0).add(
            Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
        )
    )

    # Queries and deletion
    camera = scene.get_by_name('camera1')
    assert(camera.find('transform').find('look_at').get('up') == "0 1 0")
    look_at = camera.find('transform').find('look_at')
    camera.find('transform').remove(look_at)
    camera.find('transform').add(Look_At(origin=[1,1,1], target=[1,1,1], up=[0,1,0]))
    assert(len(camera.find('transform').findall('look_at')) == 1)

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

    assert(scene.find('bsdf') and scene.find('environment') and scene.find('edf'))

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

    assert(len(config.find('configuration').findall('parameter')) == 3)
    assert(len(config.get_by_name('base_interactive').findall('parameter')) == 3)

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

    assert(len(config.get_by_name('base_final')\
        .get_by_name('light_engine')\
        .find('parameters').\
        findall('parameter') ) == 2)

    #
    project.add(config)
    # We're done:
    # print project
    xml = project.tostring()

    # with open(filename, 'w') as file: 
    #     file.write(xml) etc...


    # Higher level interface (happleseed.py)
    # TODO: delegate candidates for higher life existance: 
    # cameras, lights, configs, spectral colors?
    import happleseed
    scene   = Scene()
    project = Project().add(scene)

    # FIXME Scene won't be found unless it's not empty (see bellow
    # assert(project.find('scene')) 
    # This works though
    assert(project.findall('scene'))
    assert(len(project.findall('scene')) == 1)

    # (1) happleseend.Callable() returns HapsObj
    camera = happleseed.ThinLensCamera('renderCam', film_dimensions=[0.2, .3])
    scene.add(camera)
    # This works with items added. 
    assert(project.find('scene')) 

    # (2) maybe with explicite factory (does it bring much to the table?)
    # We need hierarchy insertion constrain
    scene = Scene()
    scene.add(happleseed.Factory('Frame','beauty', 
        parms=(('resolution' ,[1920, 1080]),), 
        camera='renderCam2'))
    scene.add(happleseed.Factory('Camera', 'renderCam2', 
        parms=(('aspect_ratio',1), ), model="pinhole_camera"))

    assert(scene.find('camera'))
    assert(scene.find('frame').get_by_name('resolution').get('value') == [1920, 1080])

    # (3) or more object oriented?
    apple = happleseed.AppleSeed()
    apple.scene = Scene()

    # How about create context with parent, is it general? 
    apple.assembly = Assembly('assembly')
    apple.project.add(apple.scene)
    apple.scene.add(apple.assembly)  

    assert(splitXMLtoWords(str(apple.project)) == minimal_project)

    #  via factory() method:
    # by default first assembly is a scene:
    light = apple.factory('scene').create('Light', 'lamp', model='point_light')
    print light
    # This addes three objects:
    env = apple.factory('scene').create('Environment', 'preetham_env', turbidity=2.0)
    # print env
    # len(objects) == 3
    objects = happleseed.Environment('preetham_env', turbidity=2.0) 
    assert(len(objects) == 3)
    # This for example is not valided with Appleseed schema: 
    # apple.factory('scene').create('MeshObject'))
    mesh = apple.factory().create('MeshObject','mesh1', filename="mesh.obj")

    quit()

    # Yet another way
    apple = happleseed.AppleSeed()
    apple.Scene().add('Environment', 'preetham_env', turbidity=2.0)
    apple.Assembly('assembly').add('Light', 'sun', model='point_light')
    apple.Assembly().add('MeshObject', 'torus', filename='torus.obj')
    apple.scene.add(Assembly('new_assembly'))
    apple.scene.add(Assembly_Instance('na_inst', assembly='new_assembly'))
    apple.Assembly('new_assembly').add('MeshObject', 'torus2', filename='torus.obj')
    apple.Config().insert('InteractiveConfiguration', 'base_interactive')

    # Replace one element:
    apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='nonsense')
    # assert(apple.project.find('configurations').get_by_name('base_interactive')\
    #     .get_by_name('lighting_engine').get('value') == 'nonsense')
    # apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='ptt')
    # assert(apple.project.find('configurations').get_by_name('base_interactive')\
    #     .get_by_name('lighting_engine').get('value') == 'ptt')


    apple.Output().insert('Frame', 'beauty', resolution=[1920, 1080])
    assert(apple.project.find('output'))
    assert(apple.project.find('output').get_by_name('beauty')\
        .get_by_name('resolution').get('value') == '1920 1080')


    apple.Assembly().insert('DisneyMaterial', 'some_disney_material', base_color=[1,0,0])
    assert(apple.assembly.find('material'))
    assert(apple.assembly.find('material').get('name') == 'some_disney_material')
    assert(apple.assembly.get_by_name('some_disney_material').get('model')  == 'disney_material')

    with open('test.appleseed', 'w') as file:
        file.write(apple.project.toxml())
        file.close()

    # How to get to subelements:
    max_bounces = apple.config.get_by_name('base_interactive')\
        .get_by_name('pt')\
        .get_by_name('max_bounces')\
        .get('value')

    assert(max_bounces == '-1')
    # Debug with line number
    counter = 1
    # for line in str(apple.project).split('\n'):
    #     print str(counter) + "   " + line
    #     counter += 1


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
