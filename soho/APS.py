import sys, os

import time
import soho
import sohog
import hou
from soho import SohoParm

GEOPATH   = os.path.join(os.getcwd(), 'tmp')
EXTENSION = ".obj" # TODO replace with .appleseed

# IFDhooks.call("pre_ifdGen")
clockstart = time.time()


controlParameters = {
    # The time at which the scene is being rendered
    'now'     : SohoParm('state:time', 'real',  [0], False,  key='now'),

    # The mode (default, rerender generate, rerender update)
    'mode'    : SohoParm('state:previewmode', 'string', ['default'], False, key='mode'),

    # A string with names of style sheets changed since the last IPR update.
    'dirtystylesheets' : SohoParm('state:dirtystylesheets', 'string', [''], False, key='dirtystylesheets'),

    # A string with names of bundles changed since the last IPR update.
    'dirtybundles' : SohoParm('state:dirtybundles', 'string', [''], False, key='dirtybundles'),

    # The camera (or list of cameras), and masks for visible objects,
    # active lights and visible fog objects
    'camera'  : SohoParm('camera', 'string', ['/obj/cam1'], False),

    # Whether to generate:
    #   Shadow maps for the selected lights
    #   Environment maps for the selected objects
    #   The main image from the camera
    #   A PBR render target
    'shadow'  : SohoParm('render_any_shadowmap','int', [1], False,key='shadow'),
    'env'     : SohoParm('render_any_envmap',   'int', [1], False,key='env'),
    'photon'  : SohoParm('render_any_photonmap', 'int', [1], False, key='photon'),
    'pointcloud'  : SohoParm('render_any_pointcloud', 'int', [1], False, key='pointcloud'),
    'main'    : SohoParm('render_viewcamera','int', [1], False, key='main'),
    'decl'    : SohoParm('declare_all_shops', 'int', [0], False, key='decl'),
    'engine'  : SohoParm('vm_renderengine',  'string', ['micropoly'],
                                            False, key='engine'),

    'vm_inheritproperties' : SohoParm('vm_inheritproperties', 'int', [0], False),

    'vm_embedvex' :SohoParm('vm_embedvex',  'int', [0], False, key='embedvex'),
    'vm_quickexit':SohoParm('vm_quickexit', 'int', [1], False),
    'vm_numpathmap':SohoParm('vm_numpathmap', 'int', [0], False),
    'vm_isuvrendering':SohoParm('vm_isuvrendering', 'bool', [False], False),
    'vm_defaults' : SohoParm('vm_defaults', 'string',
                            ['RenderProperties.json'], False),
}

parmlist = soho.evaluate(controlParameters)
options = {}
now = parmlist['now'].Value[0]
mode = parmlist['mode'].Value[0]
camera  = parmlist['camera'].Value[0]
quickexit = parmlist['vm_quickexit'].Value[0]
propdefs = parmlist['vm_defaults'].Value[0]


if not soho.initialize(now, camera, options):
    soho.error("Unable to initialize rendering module with given camera")


#
# Add objects to the scene, we check for parameters on the viewing
# camera.  If the parameters don't exist there, they will be picked up
# by the output driver.
#
objectSelection = {
    # Candidate object selection
    'vobject'     : SohoParm('vobject', 'string',       ['*'], False),
    'alights'     : SohoParm('alights', 'string',       ['*'], False),
    'vfog'        : SohoParm('vfog',    'string',       ['*'], False),

    'forceobject' : SohoParm('forceobject',     'string',       [''], False),
    'forcelights' : SohoParm('forcelights',     'string',       [''], False),
    'forcefog'    : SohoParm('forcefog',        'string',       [''], False),

    'excludeobject' : SohoParm('excludeobject', 'string',       [''], False),
    'excludelights' : SohoParm('excludelights', 'string',       [''], False),
    'excludefog'    : SohoParm('excludefog',    'string',       [''], False),

    'matte_objects'   : SohoParm('matte_objects', 'string',     [''], False),
    'phantom_objects' : SohoParm('phantom_objects', 'string',   [''], False),

    'sololight'     : SohoParm('sololight',     'string',       [''], False),

    'vm_cameralist' : SohoParm('vm_cameralist', 'string',       [''], False),
}

for cam in soho.objectList('objlist:camera'):
    break
else:
    soho.error("Unable to find viewing camera for render")



objparms = cam.evaluate(objectSelection, now)
stdobject = objparms['vobject'].Value[0]
stdlights = objparms['alights'].Value[0]
stdfog = objparms['vfog'].Value[0]
forceobject = objparms['forceobject'].Value[0]
forcelights = objparms['forcelights'].Value[0]
forcefog = objparms['forcefog'].Value[0]
excludeobject = objparms['excludeobject'].Value[0]
excludelights = objparms['excludelights'].Value[0]
excludefog = objparms['excludefog'].Value[0]
sololight = objparms['sololight'].Value[0]
matte_objects = objparms['matte_objects'].Value[0]
phantom_objects = objparms['phantom_objects'].Value[0]
forcelightsparm = 'forcelights'
if sololight:
    stdlights = excludelights = ''
    forcelights = sololight
    forcelightsparm = 'sololight'


# Obtain the list of cameras through which we need to render. The main camera
# may specify a few sub-cameras, for example, in the stereo camera case.
camera_paths = objparms['vm_cameralist'].Value[0].split()
camera_list  = []
for cam_path in camera_paths:
    camera_list.append( soho.getObject( cam_path ))
if len( camera_list ) == 0:
    cam.storeData('NoFileSuffix', True)
    camera_list.append( cam )

# First, we add objects based on their display flags or dimmer values
soho.addObjects(now, stdobject, stdlights, stdfog, True,
    geo_parm='vobject', light_parm='alights', fog_parm='vfog')
soho.addObjects(now, forceobject, forcelights, forcefog, False,
    geo_parm='forceobject', light_parm=forcelightsparm, fog_parm='forcefog')

# Force matte & phantom objects to be visible too
if matte_objects:
    soho.addObjects(now, matte_objects, '', '', False,
        geo_parm='matte_objects', light_parm='', fog_parm='')
if phantom_objects:
    soho.addObjects(now, phantom_objects, '', '', False,
        geo_parm='phantom_objects', light_parm='', fog_parm='')
soho.removeObjects(now, excludeobject, excludelights, excludefog,
    geo_parm='excludeobject', light_parm='excludelights', fog_parm='excludefog')

# site-wide customization hook
# IFDhooks.call('pre_lockObjects', parmlist, objparms, now, camera)

# Lock off the objects we've selected
soho.lockObjects(now)

# IFDsettings.clearLists()
# IFDsettings.initializeFeatures()
# IFDsettings.setMattePhantomOverrides(now, matte_objects, phantom_objects)

# IFDmisc.initializeMotionBlur(cam, now)

FPS = soho.getDefaultedFloat('state:fps', [24])[0]
FPSinv = 1.0 / FPS

import haps
import APSframe as APSobj


aps = APSobj.Appleseed()
scene = aps.scene
assembly = aps.assembly

def get_obj_filename(obj, group='', ext=EXTENSION):
    objectname = obj.getName().replace("/", "_")[1:] + group + ext
    return os.path.join(GEOPATH, objectname)


camera_parms = {'film_dimensions': (cam.getDefaultedInt('res', now, [0,0])[0],
                                    cam.getDefaultedInt('res', now, [0,0])[1])
    
            ,   'shutter_open_time':  0.0 # FIXME (in mantra this lives on rop)
            ,   'shutter_close_time': cam.getDefaultedFloat('shutter', now, [0])[0]
            ,   'aspect_ratio':       cam.getDefaultedFloat('aspect', now, [1])[0]
            ,   'focal_length':       cam.getDefaultedFloat('focal', now, [24])[0] * 30
            ,   'near_z':             cam.getDefaultedFloat('near', now, [0.1])[0] * -1
    }


##### CAMERA - Pinhole camera - for now ###################
camera = APSobj.PinholeCamera(cam.getName(), **camera_parms)
xform  = []
if cam.evalFloat("space:world", now, xform):
    camera.add(haps.Transform(time=now).add(
        haps.Matrix(xform)))

scene.add(camera)
assembly.add(APSobj.DefaultLambertMaterial('default_material'))

##### Basic objects - /obj level - #############################
for obj in soho.objectList('objlist:instance'):
    soppath = obj.getDefaultedString('object:soppath', now, [''])[0]
    gdp     = sohog.SohoGeometry(soppath, now)
    if gdp.Handle < 0:
        sys.stderr.write("No geometry to reach in {}!".format(obj.getName()))
        continue

    parts = gdp.partition('geo:partattrib', 'shop_materialpath')
	#gdp.tesselate({'geo:convstyle':'lod', 'geo:triangulate':True})
    options = { "geo:saveinfo":False, 
                "json:textwidth":0, 
                "geo:skipsaveindex":True, 
                'savegroups':True, 
                'geo:savegroups':True}

    # for group, part in parts.items():
    #     group = group.replace('/', '_')
    # sys.stderr.write(filename)
    filename = get_obj_filename(obj, '')
    if not gdp.save(filename, options):
        sys.stderr.write("Can't save geometry from {} to {}".format(soppath, filename))
        continue

    xform = []
    obj.evalFloat("space:world", now, xform)
    aps.Assembly().insert('MeshObject', obj.getName(), 
        filename=filename, xform=haps.Matrix(xform))

###### Basic lights ######################################
for light in soho.objectList('objlist:light'):
    xform = []
    light.evalFloat('space:world', now, xform)
    aps.Assembly().insert('PointLight', light.getName(), xform=haps.Matrix(xform))

############ - Frame - basics - ##################################
aps.Output().insert('Frame', 'beauty', resolution=camera_parms['film_dimensions'], 
    crop_window=(0,0,camera_parms['film_dimensions'][0], camera_parms['film_dimensions'][1]),
    camera=camera.get('name'))


########## - Render configuration - ######################################
aps.Config().insert('FinalConfiguration', 'final')
aps.Config().insert('InteractiveConfiguration', 'interactive')

with open('/tmp/aps.appleseed', 'w') as file:
    file.write(str(aps.project))






















