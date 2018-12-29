import unittest
import sys
sys.path.append('/Users/symek/work/haps/soho')
import haps
import APSframe



class APSframeTestCase(unittest.TestCase):
    def setUp(self):
        self.minimal_project = ['<project format_revision="%i">' % haps.FORMAT_REVISION, '<scene>', 
            '<assembly_instance name="assembly_inst" assembly="assembly">','<transform time="0">',
            '<matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>',
            '</transform>', '</assembly_instance>','<assembly name="assembly"/>', 
            '</scene>', '</project>']

    def splitXMLtoWords(self, xml, whitespace='\n'):
        return [word.strip() for word in \
            str(xml).split(whitespace) if word != ""]

    
    def test_thinlenscamera_updating_arguments(self):
        from APSframe import ThinLensCamera
        camera1 = APSframe.ThinLensCamera('camera', film_dimensions='0.2 .3')
        camera2 = APSframe.ThinLensCamera('camera')
        self.assertNotEqual(str(camera2), str(camera1))

    def test_creation_composed_objects(self):
        objects = APSframe.Environment('preetham_env', turbidity=2.0) 
        self.assertEqual(len(objects), 3)

    def test_free_standing_factory_method(self):
        from haps import Scene
        scene = Scene()
        scene.add(APSframe.Factory('Frame','beauty', parms=(('resolution' ,[1920, 1080]),), camera='renderCam2'))
        scene.add(APSframe.Factory('Camera', 'renderCam2', parms=(('aspect_ratio',1), ), model="pinhole_camera"))
    
        self.assertIsNotNone(scene.find("frame"))
        self.assertIsNotNone(scene.find("camera"))
        self.assertEqual(scene.find('camera').get('model'), 'pinhole_camera')
        self.assertEqual(scene.find('frame').get_by_name('resolution').get('value'), [1920, 1080]) 

    def test_setup_appleseed_object(self):
        from haps import Project, Scene, Assembly, Assembly_Instance, Transform, Matrix
        apple = APSframe.Appleseed()
        # apple is atm equal to this:
        project = Project()
        scene   = Scene()
        project.add(scene)
        scene.add(Assembly('assembly')).add(
            Assembly_Instance('assembly_inst', assembly='assembly').add(
                Transform().add(Matrix())))
        
        self.assertEqual(apple.assembly, Assembly('assembly'))
        self.assertEqual(apple.project, project)

    def test_scene_factory(self):
         # Scene returns factory class which is trained to add objects into right place
        apple = APSframe.Appleseed()
        apple.Scene().add('Environment', 'preetham_env', turbidity=2.123)

        self.assertIsNotNone(apple.scene.find('environment'))
        self.assertIsNotNone(apple.scene.find('environment_edf'))
        self.assertIsNotNone(apple.scene.find('environment_shader'))
        self.assertEqual(apple.scene.find('environment_edf').get_by_name('turbidity').get('value'), 2.123)

    def test_assembly_factory(self):
        apple = APSframe.Appleseed()
        apple.Assembly('assembly').add('Light', 'sun', model='point_light')
        self.assertEqual(apple.assembly.find('light'), apple.assembly.get_by_name('sun'))

    def test_assembly_factory_create_method(self):
        from haps import Matrix
        apple = APSframe.Appleseed()
        objects1 = apple.Assembly().create('MeshObject', 'torus', filename='torus.obj')
        objects2 = apple.Assembly().create('MeshObject', 'torus', filename='torus.obj', xform=Matrix())
        self.assertEqual(''.join(map(str, objects1)), ''.join(map(str, objects2)))

    def test_assembly_factory_motion_blur(self):
        from haps import Matrix
        apple = APSframe.Appleseed()
        # Motion blur
        xforms = [Matrix() for step in range(5)]
        apple.Assembly('new_assembly').insert('MeshObject', 'moving_box', filename='box.obj', xforms=xforms)
        self.assertEqual(len(apple.scene.get_by_name('new_assembly').get_by_name('moving_box_inst').findall('transform')), 5)

    def test_find_instances(self):
        from haps import Matrix
        apple = APSframe.Appleseed()
        xforms = [Matrix() for step in range(5)]
        apple.Assembly('new_assembly').insert('MeshObject', 'moving_box', filename='box.obj', xforms=xforms)
     
        # How to easiliy get to object instances?
        instances = [inst for inst in apple.scene.get_by_name("new_assembly")\
            .findall('object_instance') if inst.get('object') == 'moving_box.0']
        self.assertIsNotNone(instances)

        # TODO: add easy duplicating (via deecopy) with auto renaming.

        self.assertEqual(len(apple.scene.findall('assembly')), 2)
        self.assertEqual(len(apple.scene.findall('assembly_instance')), 2)
        self.assertIsNotNone(apple.scene.get_by_name('new_assembly'))

    def test_replace_partial_config(self):
        apple = APSframe.Appleseed()
        apple.Config().insert('InteractiveConfiguration', 'base_interactive')

        # Replace one element:
        apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='nonsense')
        self.assertEqual(apple.project.find('configurations').get_by_name('base_interactive')\
            .get_by_name('lighting_engine').get('value'), 'nonsense')

        # Replace again
        apple.Config('base_interactive').insert('Parameter', 'lighting_engine', value='ptt')
        self.assertEqual(apple.project.find('configurations').get_by_name('base_interactive')\
            .get_by_name('lighting_engine').get('value'), 'ptt')

        max_bounces = apple.config.get_by_name('base_interactive')\
        .get_by_name('pt')\
        .get_by_name('max_bounces')\
        .get('value')
        self.assertEqual(max_bounces , '-1')

    def test_output_factory(self):
        apple = APSframe.Appleseed()
        apple.Output().insert('Frame', 'beauty', resolution=[1920, 1080])
        self.assertIsNotNone(apple.project.find('output'))
        self.assertEqual(apple.project.find('output').get_by_name('beauty')\
        .get_by_name('resolution').get('value') , '1920 1080')

    def test_composed_materials(self):
        apple = APSframe.Appleseed()
        apple.Assembly().insert('DisneyMaterial', 'some_disney_material', base_color=[1,0,0])
        self.assertIsNotNone(apple.assembly.find('material'))
        self.assertEqual(apple.assembly.find('material').get('name'), 'some_disney_material')
        self.assertEqual(apple.assembly.get_by_name('some_disney_material').get('model') , 'disney_material')
        # FIXME: unify numeric parameters, now sometimes they are early rendered to strings sometimes not.
        self.assertEqual(apple.assembly.get_by_name('some_disney_material')\
            .find('parameters').get_by_name('base_color').get('value'), "1 0 0") # BUG
























