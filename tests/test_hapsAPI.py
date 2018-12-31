import unittest
import sys
sys.path.append('soho')
import haps



class HapsApiTestCase(unittest.TestCase):
    def setUp(self):
        
        self.minimal_project = ['<project format_revision="%i">' % haps.FORMAT_REVISION, '<scene>', 
        '<assembly name="assembly"/>', '</scene>', '</project>']
        self.empty_project = ['<project format_revision="{}"/>'.format(haps.FORMAT_REVISION)]

    def splitXMLtoWords(self, xml, whitespace='\n'):
        return [word.strip() for word in \
            str(xml).split(whitespace) if word != ""]

    def test_empty_project(self):
        project = haps.Project()
        self.assertEqual(self.splitXMLtoWords(str(project)), self.empty_project, "These should be equal")

    def test_minimal_project(self):
        from haps import Project, Scene, Assembly
        project = Project()
        scene   = Scene()
        project.add(scene)
        assembly = Assembly('assembly')
        scene.add(assembly)
        self.assertEqual(self.splitXMLtoWords(str(project)), self.minimal_project, "These should be equal")

    def test_empty_scene_cant_be_found(self):
        from haps import Scene, Project
        scene   = Scene()
        project = Project().add(scene)

        # FIXME this is fixed
        # self.assertIsNotNone(project.find('scene')) 
        # This works though
        self.assertIsNotNone(project.findall('scene'))
        self.assertEqual(len(project.findall('scene')), 1)


    def test_first_arg_is_name(self):
        from haps import Object, Parameter
        object1  = Object(name='torus', model='mesh_object').add(Parameter('filename', 'torus.obj'))
        object2  = Object('torus', model='mesh_object').add(Parameter('filename', 'torus.obj'))
        self.assertEqual(object1, object2)

    def test_add_multiply_objects(self):
        # Add objects, its instance and defaulf transform:
        from haps import Assembly, Object, Object_Instance, Transform, Matrix
        assembly   = Assembly()
        object1    = Object('box', model='mesh_object').add_parms([('filename', 'box.obj')])
        obj1_inst1 = Object_Instance('inst_'+'torus', object='box').add(Transform().add(Matrix()))
        assembly.add([object1, obj1_inst1])

        self.assertIsNotNone(assembly.find('object')) 
        self.assertIsNotNone(assembly.find('object_instance'))
        self.assertIsNotNone(assembly.get_by_name('box'))
        self.assertIsNotNone(assembly.get_by_name('inst_torus'))

    def test_default_matrix_init_with_identity(self):
        from haps import Matrix, Transform
        ident = (1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
        self.assertEqual(str(Transform().add(Matrix())), str(Transform().add(Matrix(ident))))

    def test_reference_object_equal_reference_its_name(self):
        from haps import Object_Instance, Object
        object1   = Object('box', model='mesh_object').add_parms([('filename', 'box.obj')])
        obj_inst1 = Object_Instance('obj_inst1', object='box')
        obj_inst2 = Object_Instance('obj_inst1', object=object1)
        self.assertEqual(str(obj_inst1), str(obj_inst2))

    def test_spaghetti_addition(self):
        # Assembly spaggeti addition (ugly but handy)
        from haps import Assembly, Color, Alpha, Parameter, Values
        assembly = Assembly()
        assembly.add(Color('red').add(Alpha([1])).add(
                    Parameter('color_space', 'sRGB')).add(
                        Values([0.1, 1, 2.0])))

        self.assertEqual(assembly.find('color').get('name') , 'red')
        self.assertEqual(assembly.find('color').find('alpha').data , [1])
        self.assertEqual(assembly.find('color').find('values').data , [0.1, 1, 2.0])


    def test_assembly_instance(self):
        from haps import Assembly, Assembly_Instance, Scene, Transform, Matrix
        scene = Scene()
        assembly = Assembly('assembly') # FIXME: This is bug, without name .find()  doesn't work.
        asmb_inst1 = Assembly_Instance(name='asm1', assembly=assembly).add(Transform().add(Matrix()))
        scene.add(assembly)
        scene.add(asmb_inst1)
        self.assertIsNotNone(scene.find('assembly_instance'))
    
    def test_searching_and_removing(self):
        from haps import Scene, Camera, Transform, Look_At
        # Row camera:
        scene = Scene()
        scene.add(Camera("camera1", model="pinhole_camera").add(
            Transform(time=0).add(
                Look_At(origin=[0,0,0], target=[1,1,1], up=[0,1,0]))
            )
        )
        # Queries and deletion
        camera = scene.get_by_name('camera1')
        self.assertEqual(camera.find('transform').find('look_at').get('up') , [0, 1, 0])
        look_at = camera.find('transform').find('look_at')
        camera.find('transform').remove(look_at)
        camera.find('transform').add(Look_At(origin=[1,1,1], target=[1,1,1], up=[0,1,0]))
        self.assertEqual(len(camera.find('transform').findall('look_at')) , 1)

    def test_spectral_color_creation(self):
        from haps import Color, Parameter, Values, Alpha, Scene
        scene = Scene()
        # Row Colours:
        spectral = Color('green')
        spectral.add(Parameter('color_space', 'spectral'))
        spectral.add(Parameter('wavelength_range', "400 700"))
        spectral.add(Values([0.092000, 0.097562, 0.095000, 0.096188, 0.097000]))
        spectral.add(Alpha([.5]))
        scene.add(spectral)
        self.assertEqual(scene.find('color').find('values').text, [0.092000, 0.097562, 0.095000, 0.096188, 0.097000])
        self.assertEqual(scene.find('color').find('alpha').text, [0.5])

    def test_materials_and_its_assigment(self):
        from haps import Bsdf, Scene, Surface_Shader, Material, Object_Instance
        from haps import Assign_Material, Environment, Environment_Shader, Edf 
        # Materials + assigment:
        scene = Scene()
        obj_inst1 = Object_Instance('inst_obj')
        scene.add(obj_inst1)
        bsdf = Bsdf('sphere_brdf', model='disney_brdf')
        scene.add(bsdf)
        scene.add(Surface_Shader('sphere_shader', brdf=bsdf))
        scene.add(Material('greenish', surface_shader='sphere_shader'))
        obj_inst1.add(Assign_Material(slot='Default', side='front', material='greenish'))

        self.assertIsNotNone(scene.find('bsdf'))
        self.assertEqual(scene.find('object_instance').find('assign_material').get('material'), 'greenish')

    def test_environment_and_edf(self):
        # Env + env_shader + Edf
        from haps import Environment_Shader, Environment, Edf, Scene
        scene = Scene()
        scene.add(Environment('env', environment_shader='env_shader')).add(
            Environment_Shader('env_shader', edf='edf')).add(Edf('edf', model='cone_edf'))

        self.assertIsNotNone(scene.find('environment'))
        self.assertIsNotNone(scene.find('edf'))

    def test_frame(self):
        from haps import Project, Frame, Parameter, Output
        project = Project()
        frame = Frame('beauty').add(
        Parameter('camera', 'camera')).add(
        Parameter('resolution', '1024 1024')).add(
        Parameter('gamma_correction', "2.2"))

        # is a part of output section:
        project.add(Output().add(frame))
        self.assertIsNotNone(project.find('output'))
        self.assertIsNotNone(project.find('output').find('frame'))

    def test_basic_configuration(self):
        from haps import Configurations, Configuration, Parameter, Parameters

        # There is config and number of configs inside:
        # Also we could get rid of Parameters (as some
        # types have so many of them) with HapsObj.add_parms([...])
        config = Configurations()
        config.add(Configuration('base_interactive').add_parms([
            ('frame_renderer', 'generic'), 
            ('tile_renderer', 'generic'),
            ('pixel_renderer', 'uniform')]))

        self.assertEqual(len(config.find('configuration').findall('parameter')), 3)
        self.assertEqual(len(config.get_by_name('base_interactive').findall('parameter')), 3)

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

        self.assertEqual(len(config.get_by_name('base_final').get_by_name(
            'light_engine').find('parameters').findall('parameter') ) , 2)







 