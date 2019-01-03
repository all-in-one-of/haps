import soho
from soho import SohoParm
#TODO: move it to version.py
__version__            = '0.1-alpha'
__appleseed_version__  = "2.0-beta"


PREAMBULE="""<?xml version="1.0" encoding="UTF-8"?>
<!-- File created by Houdini: {houdini_version}
             Generation Time: {date}
               Render Target: {renderer_version} 
            APS soho version: {aps_version}
               Output driver: {driver}
                    HIP File: {hipfile}, $T={TIME}, $FPS={FPS}
-->
"""

oshaderSkipParms = {
    'shop_surfacepath' : SohoParm('shop_disable_surface_shader',  
                                   'bool', [False], False, key='surface'),
    'shop_displacepath' : SohoParm('shop_disable_displace_shader', 
                                   'bool', [False], False, key='displace'),
    'vm_matteshader' : SohoParm('shop_disable_surface_shader',  
                                   'bool', [False], False, key='matteshader'),
}

oshaderMap = {       
    'shop_materialpath' : 'surface',
    'shop_surfacepath'  : 'surface',
    'shop_photonpath'   : 'surface',
    'vm_matteshader'    : 'matteshader',
    'shop_displacepath' : 'displace',
    'shop_cvexpath'     : 'cvex',
}

def outputMaterial(shop_path, now):
    if _Settings.SavedMaterials.get(shop_path, None) == None:
        shop = soho.getObject(shop_path)
        ray_start('material')
        outputObject(shop, now, name=shop_path, output_shader=True)
        if _Settings.GenerateMaterialname:
            ray_property('object', 'materialname', [shop_path])
        ray_end()
        _Settings.SavedMaterials[shop_path] = True

# Return a tuple of the shader with its shop type if the given shader type
# is not skipped for the given node - otherwise return None.
def getObjectShader(shop_path, shader_type, now):
    shop = soho.getObject(shop_path)
    print dir(shop)
    print shop.getDefaultedShader()
    skiplist = shop.evaluate(oshaderSkipParms, now)
    shader_prop = oshaderMap[shader_type]

    skip = False
    if skiplist and shader_prop in skiplist:
        skip = skiplist[shader_prop].Value[0]

    # if not skip: # TODO disabling it intentionally
    shader = []
    shop_type = []
    if shop.evalShaderAndType(shader_type, now, shader, shop_type):
        return (shader[0], shop_type[0])

    return None


def getWrangler(obj, now, style):
    wrangler = obj.getDefaultedString(style, now, [''])[0]
    if not wrangler:
        return None
    wname = wrangler
    wrangler = '%s-appleseed' % wrangler
    if style == 'light_wrangler':
        wrangler = soho.LightWranglers.get(wrangler, None)
    elif style == 'camera_wrangler':
        wrangler = soho.CameraWranglers.get(wrangler, None)
    elif style == 'object_wrangler':
         wrangler = soho.ObjectWranglers.get(wrangler, None)
    if not wrangler:
        # if not _Settings.MissingWranglers.has_key(wname):
        #     _Settings.MissingWranglers[wname] = True
        #     soho.warning('Object %s has an unsupported wrangler (%s)'
        #                 % (obj.getName(), wname))
        return None
    return wrangler(obj, now, theVersion)