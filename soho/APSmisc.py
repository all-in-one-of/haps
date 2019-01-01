# Mostly copied from IFDmisc
import soho

def initializeMotionBlur(cam, now):
    #
    # Initialize motion blur settings from the main camera.
    #
    # global      CameraShutter, CameraShutterOffset, CameraShutterF
    # global      CameraStyle, CameraDelta, CameraBlur
    # global      FPS, FPSinv

    # IFDhooks.call('pre_initialize', cam, now)

    FPS = soho.getDefaultedFloat('state:fps', [24])[0]
    FPSinv = 1.0 / FPS

    CameraBlur,CameraDelta,CameraShutter,CameraShutterOffset,CameraStyle = \
        _getBlur(cam, now, shutter=.5, offset=None, style='trailing', allow=0, FPSinv=FPSinv)
    CameraShutterF = CameraShutter*FPS

    result = {'camer_blur': CameraBlur, 
              'camera_delta': CameraDelta, 
              'camera_shutter': CameraShutter,
              'camera_shutter_offset': CameraShutterOffset, 
              'camera_style': CameraStyle,
              'camera_shutter_fps': CameraShutterF 
              }

    return result


def _getBlur(obj, now, shutter=.5, offset=None, style='trailing', allow=1, FPSinv=1.0/24):
    allow = obj.getDefaultedInt('allowmotionblur', now, [allow])[0]
    shadowtype = obj.getDefaultedString('shadow_type', now, ['off'])[0]
    shutter = obj.getDefaultedFloat('shutter', now, [shutter])[0]*FPSinv
    offset = obj.getDefaultedFloat('shutteroffset', now, [offset])[0]
    style   = obj.getDefaultedString('motionstyle', now, [style])[0]
    if style == 'centered':
        delta = shutter * .5
    elif style == 'leading':
        delta = shutter
    else:
        delta = 0
    if offset is not None:
        # shutterOffset maps -1 to leading blur 0 to center, and +1 to trailing
        delta -= (offset - 1) * 0.5 * shutter
   
    if shadowtype == 'depthmap' and not isPreviewMode():
        shadowblur = obj.getDefaultedInt('shadowmotionblur', now, [1])[0]
        if shadowblur == False:
            allow = False
    if shutter == 0:
        allow = False
    return allow, delta, shutter, offset, style