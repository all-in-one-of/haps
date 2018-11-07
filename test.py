from haps import *



def main():
    # 
    project  = Project()
    scene    = Scene()
    assembly = Assembly('assembly')

    # First argument is always a name: 
    object1  = Object(name='mesh1', file='mesh1.obj')
    # So we can drop it
    object2  = Object('mesh2', file='mesh2.obj')
    assembly.add([object1, object2])
    scene.add(assembly)

    # 
    obj_inst1 = Object_Instance(name='obj_inst1', object=object1)
    obj_inst1.add(Transform().add(Matrix()))
    obj_inst2 = Object_Instance('obj_inst2', object=object2)
    obj_inst2.add(Transform(.5).add(Matrix(1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16)))
    assembly.add([obj_inst1, obj_inst2])

    # Assembly spageti addition:
    assembly.add(Color('red').add(Alpha(1)).add(
                Parameter('color_space', 'sRGB')).add(
                    Values([0.1, 1, 2.0])
            )
        )
    #
    asmb_inst1 = Assembly_Instance('asm1', assembly=assembly).add(Transform().add(Matrix()))
    scene.add(asmb_inst1)

    # Camera:
    scene.add(Camera("camera1", model="pinhole_camera").add(
        Transform(time=0).add(
            Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
        )
    )

    # Colours:
    spectral = Color('green')
    spectral.add(Parameter('color_space', 'spectral'))
    spectral.add(Parameter('wavelength_range', [400, 700]))
    spectral.add(Values([0.092000, 0.097562, 0.095000, 0.096188, 0.097000]))
    spectral.add(Alpha([.5]))
    scene.add(spectral)

    # Materials:
    bsdf = Bsdf('sphere_brdf', model='disney_brdf')
    scene.add(bsdf)

    # TODO: Could we also reference objects, not only their names (buggy atm)
    scene.add(Surface_Shader('sphere_shader', brdf=bsdf))
    scene.add(Material('greenish', surface_shader='sphere_shader'))
    obj_inst1.add(Assign_Material(slot='Default', side='front', material='greenish'))

    # Env
    scene.add(Environment('env', environment_shader='env_shader')).add(
        Environment_Shader('env_shader', edf='edf')).add(Edf('edf', model='cone_edf'))
    project.add(scene)

    # Frame...
    frame = Frame('beauty').add(
        Parameter('camera', 'camera')).add(
        Parameter('resolution', '1024 1024')).add(
        Parameter('gamma_correction', "2.2"))

    # is a part of output section:
    project.add(Output().add(frame))

    # There is configs and number of configs inside:
    # Also we could get rid of Parameters objects...
    config = Configurations()
    config.add(Configuration('base_interactive').add_parms([
        ('frame_renderer', 'generic'), 
        ('tile_renderer', 'generic'),
        ('pixel_renderer', 'uniform')]))

    config.add(Configuration('base_final').add([
        Parameter('frame_renderer', 'generic'),
        Parameter('tile_renderer',  'generic'),
        Parameter('pixel_renderer', 'uniform'),
        Parameter('light_engine', 'pt').add(
            Parameter('pt').add([
                Parameter('dl_light_samples', 1), 
                Parameter('enable_ibl', "true")])
            )
        ])
    )

    project.add(config)

    print project
    import happleseed
    project = Project()
    scene   = Scene()
    camera, tmp = happleseed.ThinLensCamera('renderCam')
    scene.add(camera)
    sunlight, tmp = happleseed.SunLight('sun')
    scene.add(sunlight)


    apple = happleseed.AppleSeed()
    apple.create('SunLight', 'sunlight1', cast_indirect_light='false')
    # print apple
    print apple.project
    # scene.add(happleseed.Factory('Frame','beauty', camera='renderCam2', parms=(('resolution' ,[1920, 1080]))))
    # scene.add(happleseed.Factory('Camera', 'renderCam2', model="pinhole_camera", parms=(('aspect_ratio',1))))

    

    # project.add(scene)
    # print project
    # dumps_schema()



if __name__ == "__main__": main()