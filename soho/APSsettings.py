import soho

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