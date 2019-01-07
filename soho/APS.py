import sys, os

import time
import soho
import sohog
import hou
from soho import SohoParm
from datetime import datetime


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

if mode != 'default':
    # Don't allow for nested evaluation in IPR mode
    inheritedproperties = False
else:
    inheritedproperties = parmlist['vm_inheritproperties'].Value[0]

options = {}
if inheritedproperties:
    # Turn off object->output driver inheritance
    options['state:inheritance'] = '-rop'
if propdefs and propdefs != 'stdin':
    options['defaults_file'] = propdefs

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
# import IFDsettings
# IFDsettings.clearLists()
# IFDsettings.initializeFeatures()
# IFDsettings.setMattePhantomOverrides(now, matte_objects, phantom_objects)

# IFDmisc.initializeMotionBlur(cam, now)

import haps
import APSframe
import APSmisc
import APSobj
import APSsettings

reload(APSframe)
reload(APSmisc)
reload(haps)
reload(APSobj)
reload(APSsettings)

FPS = soho.getDefaultedFloat('state:fps', [24])[0]
FPSinv = 1.0 / FPS

aps = APSobj.Appleseed()
scene    = aps.scene
assembly = aps.assembly


def exportSOPMaterial(assembly, material_path):
    # tmp
    material = APSobj.DefaultLambertMaterial(material_path)
    assembly.add(material)
    return material


from math import atan, degrees
aperture = cam.getDefaultedFloat('aperture', now, [1])[0]
focal    = cam.getDefaultedFloat('focal', now, [24])[0]
fovx     =  2 * atan((aperture/2) / focal)    
camera_parms = {'shutter_open_time' : 0.0 # FIXME (in mantra this lives on rop)
            ,   'shutter_close_time': cam.getDefaultedFloat('shutter', now, [0])[0]
            ,   'film_dimensions'   : (cam.getDefaultedInt('res', now, [0,0])[0] / 100.0, 
                                       cam.getDefaultedInt('res', now, [0,0])[1] / 100.0)
            ,   'focal_length'      : cam.getDefaultedInt('focal', now, [0,0])[0] / 100.0
            ,   'horizontal_fov'    : degrees(fovx)    
            ,   'near_z'            : cam.getDefaultedFloat('near', now, [0.1])[0] * -1
    }


##### CAMERA - Pinhole camera - for now ###################
camera = APSobj.PinholeCamera(cam.getName(), **camera_parms)
xform  = []
if cam.evalFloat("space:world", now, xform):
    xform = hou.Matrix4(xform).transposed().asTuple()
    camera.add(haps.Transform(time=now).add(
        haps.Matrix(xform)))
hou_camera = hou.node(cam.getName())
scene.add(camera)

materials_collection = [] # here we track of what we already exported
unique_gdp_collection = [] # here we store unique instanceas (not fast instances)
materials_map = {}

exportSOPMaterial(assembly, APSmisc.DEFAULT_MATERIAL_NAME)
mblur_parms = APSmisc.initializeMotionBlur(cam, now)

##### Basic objects - /obj level - #############################
for obj in soho.objectList('objlist:instance'):
    def_inst_path = [None]
    obj.evalString('instancepath', now, def_inst_path)

    instancexform = [True]
    obj.evalInt('instancexform', now, instancexform)

    # Grab the geometry and output the points
    (geo, npts, attrib_map) = APSmisc.getInstancerAttributes(obj, now)
    sopid = geo.globalValue('geo:sopid')[0]
    save_gdp = False
    if sopid not in unique_gdp_collection:
        unique_gdp_collection += [sopid]
        save_gdp = True

    filename = None 
    shop_materials = []

    filename, shop_materials = APSframe.outputTesselatedGeo(obj, now, 
        mblur_parms, partition=True, save_gdp=save_gdp)
    if (None, None) == (filename, shop_materials):
        continue
    # We need to store it for other instances
    if not def_inst_path[0]:
        obj_path = obj.getName()
    else:
        obj_path = def_inst_path[0]

    # if not obj_path in materials_map:
    #     materials_map[obj_path] = shop_materials
        # export material only once
    for shop in shop_materials:
        if shop and shop not in materials_collection:
            mat = APSframe.outputMaterial(shop, now)
            if mat:
                aps.Assembly().emplace(mat)
            else:
                aps.Assembly().insert('DefaultLambertMaterial', shop)
            materials_collection += [shop]
        # Its buggy now:
        else:
            pass
            # shop_materials = ['default']

    # MB for objects
    xforms = APSmisc.get_motionblur_xforms(obj, now, mblur_parms)
    xforms = [haps.Matrix(xform) for xform in xforms]
    if save_gdp:
        aps.Assembly().insert('MeshObject', obj.getName(), filename=filename, 
            xforms=xforms, materials=shop_materials, slots=shop_materials)
    else:
        # shop_materials = materials_map[def_inst_path[0]]
        object_name = def_inst_path[0] + ".default" #!!!
        aps.Assembly().insert('MeshInstance', obj.getName(), object=object_name, 
            xforms=xforms, materials=shop_materials, slots=shop_materials)
       

        # aps.Assembly().
        #Only instance:

###### Basic lights ######################################
for light in soho.objectList('objlist:light'):
    apslight = APSframe.outputLight(light, now, mblur_parms)
    if apslight:
        aps.Assembly().emplace(apslight)
    

############ - Frame - basics - ##################################
resolution = (cam.getDefaultedInt('res', now, [0,0])[0], cam.getDefaultedInt('res', now, [0,0])[1])
aps.Output().insert('Frame', 'beauty', resolution=resolution, 
    crop_window=(0,0,resolution[0], resolution[1]),
    camera=camera.get('name'))


########## - Render configuration - ######################################
aps.Config().insert('FinalConfiguration', 'final')
aps.Config().insert('InteractiveConfiguration', 'interactive')


parm = {'diskfile': SohoParm('soho_diskfile', 'string', ['*'], False)}
parmlist = soho.evaluate(parm)
filename = parmlist['soho_diskfile'].Value[0]


# We can't emit file to stdout, because appleseed.cli currently doesn't accept stdit 
# with open(filename, 'w') as file:
# technically preambule is not part of project object:
date      = datetime.strftime(datetime.today(), "%b %d, %Y at %H:%M:%S")
stat      = '<!-- Generation time: %g seconds -->' % (time.time() - clockstart)
preambule = APSsettings.PREAMBULE.format(
    houdini_version=hou.applicationVersionString(),
    aps_version=APSsettings.__version__,
    date=date,
    renderer_version=APSsettings.__appleseed_version__,
    driver=soho.getOutputDriver().getName(),
    hipfile=hou.hipFile.name(),
    TIME=now,
    FPS=FPS,
    )

if mode == "update": 
    xform = []
    cam.evalFloat("space:world", now, xform)
    xform = hou.Matrix4(xform).transposed().asTuple()
    xform = " ".join(map(str,xform))
    print xform
else:
    # first line if stdin is (socket, mode) where 0=default, 1=ipr
    # I would love to have custom tag in appleseed.
    if mode != 'default':
        port   = str(soho.getDefaultedInt('vm_image_mplay_socketport', [0])[0])
        is_ipr = str(soho.getDefaultedInt('vm_preview', [-1])[0])
        print "{} {}".format(port, is_ipr)
    # Rest is standard xml
    print preambule
    print str(aps.project)
    # This is trimmed on aps side.
    print stat






















