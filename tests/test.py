import sys
sys.path.append('soho')
from haps import *
import json, time

""" 
    Experiments with API design for Appleseed for Houdini.
"""

def splitXMLtoWords(xml, whitespace='\n'):
    return [word.strip() for word in \
        str(xml).split(whitespace) if word != ""]

def main():
    clockstart = time.time()
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
    assert(assembly.find('color').find('alpha').data == [1])
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
    assert(camera.find('transform').find('look_at').get('up') == [0, 1, 0])
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
    xml = project.tostring()
    # with open(filename, 'w') as file: file.write(xml) etc...


    scene   = Scene()
    project = Project().add(scene)

    # FIXME Scene won't be found unless it's not empty (see bellow
    # assert(project.find('scene')) 
    # This works though
    assert(project.findall('scene'))
    assert(len(project.findall('scene')) == 1)

    # (1) APSframe.Callable() returns HapsObj (possible more than one)
    import APSframe
    camera1 = APSframe.ThinLensCamera('camera', film_dimensions='0.2 .3')
    camera2 = APSframe.ThinLensCamera('camera')
    assert(str(camera2) != str(camera1))
    # TODO: Should we check for duplicates?
    scene.add([camera1, camera2])

    assert(len(scene.findall('camera')) == 2)

    # Some APSframe method may return multiply objects: 
    objects = APSframe.Environment('preetham_env', turbidity=2.0) 
    assert(len(objects) == 3)

    # (2) maybe with explicite factory (does it bring much to the table?)
    # better since we have hide objects inside APSframe
    scene = Scene()
    scene.add(APSframe.Factory('Frame','beauty', 
        parms=(('resolution' ,[1920, 1080]),),
        camera='renderCam2'))
    scene.add(APSframe.Factory('Camera', 'renderCam2', 
        parms=(('aspect_ratio',1), ), model="pinhole_camera"))
    
    assert(scene.find("frame"))
    assert(scene.find("camera"))
    assert(scene.find('camera').get('model') == 'pinhole_camera')
    assert(scene.find('frame').get_by_name('resolution').get('value') == [1920, 1080]) 

    # Higher level interface (APSframe.py)
    # TODO: delegate candidates for higher life existance: 
    # cameras, lights, configs, spectral colors
    apple = APSframe.Appleseed()
    # old school still valid
    apple.project.add(Configurations().add(Configuration("final").add_parms([
        ('frame_renderer', 'generic'), 
        ('tile_renderer', 'generic'),
        ('pixel_renderer', 'uniform')])))

    assert(apple.project.find('configurations'))
    assert(apple.project.find('configurations').get_by_name('final')\
        .get_by_name('frame_renderer').get('value') == 'generic')

    minimal_project = ['<project format_revision="%i">' % FORMAT_REVISION, '<scene>', 
    '<assembly_instance name="assembly_inst" assembly="assembly">','<transform time="0">',
            '<matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>',
            '</transform>', '</assembly_instance>','<assembly name="assembly"/>', 
            '</scene>', '</project>']

    # Prefered way via Appleseed object
    apple = APSframe.Appleseed()
    # apple is atm equal to this:
    project = Project()
    scene   = Scene()
    project.add(scene)
    scene.add(Assembly('assembly')).add(
        Assembly_Instance('assembly_inst', assembly='assembly').add(
            Transform().add(Matrix())))
    
    assert(apple.assembly == Assembly('assembly'))
    assert(apple.project == project)

    # Scene returns factory class which is trained to add objects into right place
    apple.Scene().add('Environment', 'preetham_env', turbidity=2.123)

    assert(apple.scene.find('environment'))
    assert(apple.scene.find('environment_edf'))
    assert(apple.scene.find('environment_shader'))
    assert(apple.scene.find('environment_edf').get_by_name('turbidity').get('value')==2.123)
    
    apple.Assembly('assembly').add('Light', 'sun', model='point_light')
    assert(apple.assembly.find('light') == apple.assembly.get_by_name('sun'))

    apple.Assembly().add('MeshObject', 'torus', filename='torus.obj', \
        xform=Matrix())

    # Mesh object + mesh object instance
    objects1 = apple.Assembly().create('MeshObject', 'torus', filename='torus.obj')
    objects2 = apple.Assembly().create('MeshObject', 'torus', filename='torus.obj', xform=Matrix())
    assert(''.join(map(str, objects1)) == ''.join(map(str, objects2)))

    # Appends new assembly, its instance (with default transform) and new object into it:
    apple.Assembly('new_assembly').insert('MeshObject', 'torus2', filename='torus2.obj')

    # Motion blur
    xforms = [Matrix() for step in range(5)]
    apple.Assembly('new_assembly').insert('MeshObject', 'moving_box', filename='box.obj', xforms=xforms)
    assert(len(apple.scene.get_by_name('new_assembly')\
        .get_by_name('moving_box_inst').findall('transform')) == 5)

 
    # How to easiliy get to object instances?
    instances = [inst for inst in apple.scene.get_by_name("new_assembly")\
        .findall('object_instance') if inst.get('object') == 'moving_box.0']
    assert(instances)

    # TODO: add easy duplicating (via deecopy) with auto renaming.

    assert(len(apple.scene.findall('assembly')) == 2)
    assert(len(apple.scene.findall('assembly_instance')) == 2)
    assert(apple.scene.get_by_name('new_assembly'))

    # apple.config.add(APSframe.InteractiveConfiguration('base_interactive'))
    # FIXME this adds params, not parrent configuration ?
    apple.Config().insert('InteractiveConfiguration', 'base_interactive')

    # Replace one element:
    apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='nonsense')
    assert(apple.project.find('configurations').get_by_name('base_interactive')\
        .get_by_name('lighting_engine').get('value') == 'nonsense')

    # Replace again
    apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='ptt')
    assert(apple.project.find('configurations').get_by_name('base_interactive')\
        .get_by_name('lighting_engine').get('value') == 'ptt')


    apple.Output().insert('Frame', 'beauty', resolution=[1920, 1080])
    assert(apple.project.find('output'))
    assert(apple.project.find('output').get_by_name('beauty')\
        .get_by_name('resolution').get('value') == '1920 1080')


    apple.Assembly().insert('DisneyMaterial', 'some_disney_material', base_color=[1,0,0])
    assert(apple.assembly.find('material'))
    assert(apple.assembly.find('material').get('name') == 'some_disney_material')
    assert(apple.assembly.get_by_name('some_disney_material').get('model')  == 'disney_material')
    # FIXME: unify numeric parameters, now sometimes they are early rendered to strings sometimes not.
    assert(apple.assembly.get_by_name('some_disney_material')\
        .find('parameters').get_by_name('base_color').get('value') == "1 0 0") # BUG


    # How to get to subelements:
    max_bounces = apple.config.get_by_name('base_interactive')\
        .get_by_name('pt')\
        .get_by_name('max_bounces')\
        .get('value')
    assert(max_bounces == '-1')

    # Debug with line number
    counter = 1
    for line in str(apple.project).split('\n'):
        print str(counter) + "   " + line
        counter += 1

    print('Generation time: %g seconds' % (time.time() - clockstart))
   

    # Play with validation:
    try:
        import lxml
    except:
        print "No lxml module. Quiting now."
        quit()

    from lxml import etree
    schema_path = "../appleseed/sandbox/schemas/project.xsd"
    xml = etree.XML(apple.project.tostring())
    xmlschema_doc = etree.parse(schema_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    xmlschema.assertValid(xml)


if __name__ == "__main__": main()
