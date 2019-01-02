# Mostly copied from IFDmisc
import soho
import hou
from soho import SohoParm

import os

objXformMotion = [
    SohoParm('xform_motionsamples',     'int', [2], False),
]

HOUDINI_TEMP_DIR   = '$HOUDINI_TEMP_DIR/ifds/storage'
HOUDINI_SHARED_DIR = '$HIP/ifds/storage'

def ouputMotionBlurInfo(obj, now, CameraBlur, required=False):
    motionInfo = {
        'xform' : SohoParm('xform_motionsamples', 'int', [2], not required, key='xform'),
        'geo'   : SohoParm('geo_motionsamples',   'int', [1], not required, key='geo')
    }
    
    # Write out the number of transform and geometry motion samples
    # if motion blur is enabled.
    if CameraBlur:
        plist = obj.evaluate(motionInfo, now)
        xform = plist.get('xform', None)
        geo = plist.get('geo', None)
        nseg = xform.Value[0] if xform else 1
        if nseg > 1:
            pass
            # ray_property('object', 'xformsamples', [nseg])
        nseg = geo.Value[0] if geo else 1
        if nseg > 1:
            pass
            # ray_property('object', 'geosamples', [nseg])



def get_motionblur_xforms(obj, now, mblur_parms):
    times = xform_mbsamples(obj, now, **mblur_parms)
    xforms = []
    for t in times:
        xform = []
        obj.evalFloat("space:world", t, xform)
        xform = list(hou.Matrix4(xform).transposed().asTuple())
        xforms += [xform]
    return xforms


def _fillTime(now, nseg, delta, shutter):
    t0 = now - delta
    t1 = t0 + shutter
    times = []
    tinc = (t1 - t0)/float(nseg-1)
    for i in xrange(nseg):
        times.append(t0)
        t0 += tinc
    return times

def xform_mbsamples(obj, now, **kwargs):
    times = [now]
    CameraBlur     = kwargs.get('CameraBlur')
    CameraShutterF = kwargs.get('CameraShutterF')
    CameraShutterOffset = kwargs.get('CameraShutterOffset')
    CameraStyle   = kwargs.get('CameraStyle')

    if CameraBlur:
        allowmb,delta,shutter,offset,style = _getBlur(obj, now,
                                                shutter=CameraShutterF,
                                                offset=CameraShutterOffset,
                                                style=CameraStyle,
                                                allow=1)
        if allowmb:
            plist = obj.evaluate(objXformMotion, now)
            nseg  = plist[0].Value[0]
            if allowmb and nseg > 1:
                times = _fillTime(now, nseg, delta, shutter)
    return times

def initializeMotionBlur(cam, now):
    #
    # Initialize motion blur settings from the main camera.

    FPS = soho.getDefaultedFloat('state:fps', [24])[0]
    FPSinv = 1.0 / FPS

    CameraBlur,CameraDelta,CameraShutter,CameraShutterOffset,CameraStyle = \
        _getBlur(cam, now, shutter=.5, offset=None, style='trailing', allow=1, FPSinv=FPSinv)
    CameraShutterF = CameraShutter*FPS

    result = {'CameraBlur': CameraBlur, 
              'CameraDelta': CameraDelta, 
              'CameraShutter': CameraShutter,
              'CameraShutterOffset': CameraShutterOffset, 
              'CameraStyle': CameraStyle,
              'CameraShutterF': CameraShutterF 
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
   
    if shutter == 0:
        allow = False
    return allow, delta, shutter, offset, style


def getSharedStoragePath(TmpSharedStorage=HOUDINI_SHARED_DIR):
    TmpSharedStorage = hou.expandString(TmpSharedStorage)
    if not os.path.isdir(TmpSharedStorage):
        umask = os.umask(0)
        try:
            os.makedirs(TmpSharedStorage)
        except:
            TmpSharedStorage =hou.expandString('$HOUDINI_TEMP_DIR/ifds/storage')
            if not os.path.isdir(TmpSharedStorage):
                os.makedirs(TmpSharedStorage)
        os.umask(umask)
    return TmpSharedStorage

def getLocalStoragePath(TmpLocalStorage=HOUDINI_TEMP_DIR):
    TmpLocalStorage = hou.expandString(TmpLocalStorage)
    if not os.path.isdir(TmpLocalStorage):
        umask = os.umask(0)
        try:
            os.makedirs(TmpLocalStorage)
        except:
            TmpLocalStorage = hou.expandString('$HOUDINI_TEMP_DIR/ifds/storage')
            if not os.path.isdir(TmpLocalStorage):
                os.makedirs(TmpLocalStorage)
        os.umask(umask)
    return TmpLocalStorage


