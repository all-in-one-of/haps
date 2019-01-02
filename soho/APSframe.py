#Mostly copied from IFDframe
import soho
import haps
import APSmisc
import APSsettings
import APSobj

def outputLight(light, now, mblur_parms):
    # Find the wrangler for evaluating soho parameters
    wrangler = APSsettings.getWrangler(light, now, 'light_wrangler')
    xforms = APSmisc.get_motionblur_xforms(light, now, mblur_parms)
    xforms = [haps.Matrix(xform) for xform in xforms]

    wrangler  = APSsettings.getWrangler(light, now, 'light_wrangler')
    ltype     = light.wrangleString(wrangler, 'vm_areashape', now, [''])[0]
    exposure  = light.wrangleFloat(wrangler, 'light_exposure', now, [''])[0]
    intensity = light.wrangleFloat(wrangler, 'light_intensity', now, [''])[0]
    color     = light.wrangleFloat(wrangler, 'light_color', now, [''])
    color[0] *= intensity
    color[1] *= intensity
    color[2] *= intensity

    colorname= light.getName() + '/color'
    apscolor = APSobj.Color(colorname, values=color, alpha=1.0)
    
    light_parms = {
        'cast_indirect_light': True,
        'exposure': exposure,
        'importance_multiplier': 1.0,
        'intensity': apscolor.get('name'),
        'intensity_multiplier': 1.0    
        }

    if ltype == 'point':
        light = APSobj.PointLight(light.getName(), xforms=xforms, **light_parms)

    return light, apscolor



    # objectTransform('space:world', light, times)

    # if isGeoLight(light, wrangler, now):
    #     IFDgeo.instanceGeometry(light, now, times)

    # IFDsettings.outputObject(light, now, wrangler=wrangler)
    # IFDsettings.outputLight(wrangler, light, now)