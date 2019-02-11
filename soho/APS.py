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

motion_blur_params = APSmisc.initializeMotionBlur(cam, now)
FPS = soho.getDefaultedFloat('state:fps', [24])[0]
FPSinv = 1.0 / FPS

aps   = APSobj.Appleseed()
scene = aps.scene


Sampling = {
    'passes'                                 : soho.getDefaultedInt( 'aps_passes', [''] )[0],
    'pixel_renderer'                         : 'uniform' if not soho.getDefaultedInt( 'aps_adaptivesampling', [''] )[0] else '',
    'adaptive_tile_renderer/min_samples'     : soho.getDefaultedInt( 'aps_minsamples', ['16'] )[0],
    'adaptive_tile_renderer/max_samples'     : soho.getDefaultedInt( 'aps_maxsamples', ['265'], )[0],
    'adaptive_tile_renderer/batch_size'      : soho.getDefaultedInt( 'aps_batchsize',  ['16'] )[0],
    'adaptive_tile_renderer/noise_threshold' : soho.getDefaultedFloat( 'aps_variance', ['0.1'] )[0],
    'uniform_pixel_renderer/samples'         : soho.getDefaultedInt( 'aps_minsamples', ['16'] )[0],
    'uniform_pixel_renderer/force_antialiasing' : soho.getDefaultedInt( 'aps_uniformforceantialiasing',  ['true'] )[0],
    'uniform_pixel_renderer/decorrelate_pixels' : soho.getDefaultedInt( 'aps_uniformdecorrelatepixels',  ['true'] )[0],
    # TODO:
    # 'samplelock'      : soho.getDefaultedInt( 'aps_samplelock',  ['0'] )[0],
    # 'randomseed'      : soho.getDefaultedInt( 'aps_randomseed',  ['0'] )[0],
}


Rendering = {
    'lighting_engine'   : soho.getDefaultedString( 'aps_lightingengine', [''] )[0],
    'spectrum_mode'     : 'rgb' if not soho.getDefaultedInt( 'aps_spectrummode', [''] )[0] else 'spectral',
    'rendering_threads' : soho.getDefaultedInt( 'aps_threads',  ['0'] )[0],

}

PathTracing = {
    'pt/enable_ibl'        : 'true' if soho.getDefaultedInt( 'aps_imagebasedlighting',[True] )[0] else 'false',
    'pt/enable_dl'         : 'true' if soho.getDefaultedInt( 'aps_directlighing', [True] )[0] else 'false',
    'pt/enable_caustics'   : 'true' if soho.getDefaultedInt( 'aps_caustics', ['true'] )[0] else 'false',
    'pt/max_bounces'       : soho.getDefaultedInt( 'aps_maxbounces', [''] )[0],
    'pt/max_diffuse_bounces'    : soho.getDefaultedInt( 'aps_maxdiffusebounces', [''] )[0],
    'pt/max_glossy_bounces'     : soho.getDefaultedInt( 'aps_maxglossybounces', [''] )[0],
    'pt/max_specular_bounces'   : soho.getDefaultedInt( 'aps_maxspecularbounces', [''] )[0],
    'pt/max_volume_bounces'     : soho.getDefaultedInt( 'aps_maxvolumebounces', [''] )[0],
    'pt/dl_light_samples'       : soho.getDefaultedInt( 'aps_directlighitngsamples', [''] )[0],
    'pt/ibl_env_samples'        : soho.getDefaultedInt( 'aps_iblsamples', [''] )[0],
    'pt/rr_min_path_length'     : soho.getDefaultedInt( 'aps_rrminpathlength', [''] )[0],

}

SPPM = {
    'sppm/photon_type'       :  soho.getDefaultedString( 'aps_photontype',[''] )[0],
    'sppm/dl_mode'           :  soho.getDefaultedString( 'aps_sppmdirectlighing',['pt'] )[0],
    'sppm/enable_ibm'        : 'true' if soho.getDefaultedInt( 'aps_directlighing', [True] )[0] else 'false',
    'sppm/enable_caustics'   : 'true' if soho.getDefaultedInt( 'aps_caustics', ['true'] )[0] else 'false',
    'sppm/photon_tracing_max_bounces' : soho.getDefaultedInt( 'aps_maxphotonbounces', [''] )[0],
    'sppm/path_tracing_max_bounces'   : soho.getDefaultedInt( 'aps_maxpathbounces', [''] )[0],
    'sppm/light_photons_per_pass'     : soho.getDefaultedInt( 'aps_lightphotons', [''] )[0],
    'sppm/env_photons_per_pass'   : soho.getDefaultedInt( 'aps_environmentphotons', [''] )[0],
    'sppm/initial_radius'         : soho.getDefaultedFloat( 'aps_sppminitialradius', [''] )[0],
    'sppm/max_photons_per_estimate' : soho.getDefaultedInt( 'aps_maxphotonsperestimate', [''] )[0],
    'sppm/alpha'                    : soho.getDefaultedFloat( 'aps_sppmalpha', ['0.7'] )[0],

}
########## - Render configuration - ######################################
aps.Config().insert('FinalConfiguration', 'final')
aps.Config().insert('InteractiveConfiguration', 'interactive')

final_config = aps.config.get_by_name('final')
APSobj.update_parameters(final_config, **Rendering)
APSobj.update_parameters(final_config, **Sampling)
APSobj.update_parameters(final_config, **PathTracing)
APSobj.update_parameters(final_config, **SPPM)
# print final_config



def exportSOPMaterial(assembly, material_path):
    # tmp
    material = APSobj.DefaultLambertMaterial(material_path)
    assembly.add(material)
    return material


import math
aperture = cam.getDefaultedFloat('aperture', now, [1])[0]
focal    = cam.getDefaultedFloat('focal', now, [24])[0]
fovx     =  2 * math.atan((aperture/2) / focal)    
xforms, times = APSmisc.get_motionblur_xforms(cam, now, motion_blur_params)
allowed_mb    = motion_blur_params['CameraBlur']

camera_parms = {
            'shutter_open_begin_time'  : '0.0',
            'shutter_open_end_time'    : '0.0', 
            'shutter_close_begin_time' : '0.0' if not allowed_mb else cam.getDefaultedFloat('shutter', now, [0])[0], 
            'shutter_close_end_time'   : '0.0' if not allowed_mb else cam.getDefaultedFloat('shutter', now, [0])[0],  
            'film_dimensions'          : (cam.getDefaultedInt('res', now, [0,0])[0] / 100.0, 
                                          cam.getDefaultedInt('res', now, [0,0])[1] / 100.0),
            'horizontal_fov'          : math.degrees(fovx),  
            'near_z'                  : cam.getDefaultedFloat('near', now, [0.1])[0] * -1,
            'focal_distance'          : cam.getDefaultedFloat('focus', now, [0])[0], 
            'f_stop'                  : cam.getDefaultedFloat('fstop', now, [0])[0], 
            'xforms'                  : xforms,
            'times'                   : times,
}


##################### CAMERA  ###################
allowed_dof   = soho.getDefaultedInt( 'aps_dof', [''] )[0]
if allowed_dof:
    camera = APSobj.ThinLensCamera(cam.getName(), **camera_parms)
else:
    camera = APSobj.PinholeCamera(cam.getName(), **camera_parms)

port   = str(soho.getDefaultedInt('vm_image_mplay_socketport', [0])[0])
is_ipr = str(soho.getDefaultedInt('vm_preview', [-1])[0])

# These are custom params to notify Appleseed about our plans
camera.add_parms([
    ("socketport", port),
    ("preview",   is_ipr) # 1 for ipr 0 for normal (and -1 if render to disk)
    ])

scene.add(camera)
print aps.project
quit()

# materials_collection = [] # here we track of what we already exported
unique_gdp_collection = [] # here we store unique instanceas (not fast instances)
materials_map = {}
instance_referenced_gdps = []



##### Basic objects  and instances - TODO: HDAs? - ###########################
for obj in soho.objectList('objlist:instance'):
    def_inst_path = [None]
    obj.evalString('instancepath', now, def_inst_path)
    # Here we keep track of gpds which are not visible but referenced by instancers.
    if def_inst_path[0] not in instance_referenced_gdps:
        instance_referenced_gdps += def_inst_path
        # aps.Scene().insert("MeshObject", obj.getName(), )

    instancexform = [True]
    obj.evalInt('instancexform', now, instancexform)

    # Grab the geometry and output the points
    (geo, npts, attrib_map) = APSmisc.getInstancerAttributes(obj, now)
    sopid = geo.globalValue('geo:sopid')[0]

    # Save detail on disk only once
    unique_gdp = False
    if sopid not in unique_gdp_collection:
        unique_gdp_collection += [sopid]
        unique_gdp = True

    filename = None 
    shop_materials = []

    filename, shop_materials = APSframe.outputTesselatedGeo(obj, now, 
        motion_blur_params, partition=True, save_gdp=unique_gdp)

    #No filename nor shop material?
    if (None, None) == (filename, shop_materials):
        continue

    # MB for objects
    xforms, times  = APSmisc.get_motionblur_xforms(obj, now, motion_blur_params)
    # This assembly holds single object which won't be saved again. 
    if unique_gdp:
        assembly_materials = []
        kwargs = [{'materials': shop_materials, 
                    'slots':    shop_materials, }]

        # This object container.  
        aps.Scene().insert('AssemblyObject', obj.getName(), filenames=[filename,], 
            list_of_kwargs=kwargs, xforms=xforms, times=times)

        # If we are unique but def_instant_path is not empty
        # we have to export  source (instanced) geometry. Otherwise instances 
        # wont work with visibility flag set to False in Houdini (which is usually the case)
        if def_inst_path != [None]:
            ghost_object_name = def_inst_path[0]
            visibility_flags = {'visibility/camera':'false', 'visibility/shadow': 'false', 
                                'visibility/probe': 'false'}
            aps.Scene().insert('AssemblyObject', ghost_object_name, filenames=[filename,],
                list_of_kwargs=kwargs, **visibility_flags)
            #Not sure if we need it 
            aps.Assembly(ghost_object_name).emplace(
                APSobj.DefaultLambertMaterial(APSmisc.DEFAULT_MATERIAL_NAME))
            for shop in shop_materials:
                aps.Assembly(ghost_object_name).emplace(APSframe.outputMaterial(shop, now))

        #Add default material (again we should not need so many og them)
        aps.Assembly(obj.getName()).emplace(
            APSobj.DefaultLambertMaterial(APSmisc.DEFAULT_MATERIAL_NAME))
        #Add materials
        for shop in shop_materials:
            if shop and shop not in assembly_materials:
                mat = APSframe.outputMaterial(shop, now)
                if mat:
                    aps.Assembly(obj.getName()).emplace(mat)
                    assembly_materials += [shop]
           
    else:
        # This is an instance of the assembly object already exported.
        # Geometry mesh was exported too.
        ass_name = def_inst_path[0]
        ass_inst = haps.Assembly_Instance(obj.getName()+"_inst", assembly=ass_name)
        ass_inst = APSobj.TransformBlur(ass_inst, xforms, times)
        aps.Scene().emplace(ass_inst)
       

###### Basic lights ######################################
for light in soho.objectList('objlist:light'):
    apslight = APSframe.outputLight(light, now, motion_blur_params)
    if apslight:
        aps.Assembly().emplace(apslight)
    

############ - Frame - basics - ##################################
resolution = (cam.getDefaultedInt('res', now, [0,0])[0], cam.getDefaultedInt('res', now, [0,0])[1])
aps.Output().insert('Frame', 'beauty', resolution=resolution, 
    crop_window=(0,0,resolution[0], resolution[1]),
    camera=camera.get('name'))





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
        # this is special case for pipeing
        print aps.project.tostring(pretty_print=False)
    # Rest is standard xml
    else:
        print preambule
        print str(aps.project)
        print stat






















