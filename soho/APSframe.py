#Mostly copied from IFDframe
import soho
import sohog
import haps
import APSmisc
import APSsettings
import APSobj
import math


def outputTesselatedGeo(obj, now, mblur_parms, partition=False):
    soppath = obj.getDefaultedString('object:soppath', now, [''])[0]
    gdp     = sohog.SohoGeometry(soppath, now)
    if gdp.Handle < 0:
        sys.stderr.write("No geometry to reach in {}!".format(obj.getName()))
        return None, None

    shop_materialpaths = [None]
    if partition:
        parts = gdp.partition('geo:partattrib', 'shop_materialpath')
        shop_materialpaths = parts.keys()

    gdp.tesselate({'geo:convstyle':'div', 'geo:triangulate':False, 'tess:polysides':3})
    
    options = { "geo:saveinfo":False, 
                "json:textwidth":0, 
                "geo:skipsaveindex":True, 
                'savegroups':True, 
                'geo:savegroups':True}

    filename = APSmisc.get_obj_filename(obj, '')
    if not gdp.save(filename, options):
        sys.stderr.write("Can't save geometry from {} to {}".format(soppath, filename))
        return None, None

    return filename, shop_materialpaths


def outputLight(light, now, mblur_parms):
    # Find the wrangler for evaluating soho parameters
    wrangler = APSsettings.getWrangler(light, now, 'light_wrangler')
    xforms   = APSmisc.get_motionblur_xforms(light, now, mblur_parms)
    xforms   = [haps.Matrix(xform) for xform in xforms]

    wrangler  = APSsettings.getWrangler(light, now, 'light_wrangler')
    ltype     = light.wrangleString(wrangler, 'vm_areashape', now, [''])[0]
    exposure  = light.wrangleFloat(wrangler, 'light_exposure', now, [''])[0]
    intensity = light.wrangleFloat(wrangler, 'light_intensity', now, [''])[0]
    color     = light.wrangleFloat(wrangler, 'light_color', now, [''])
    color[0] *= intensity
    color[1] *= intensity
    color[2] *= intensity

    colorname= light.getName() + '/color'
    
    light_parms = {
        'cast_indirect_light': True,
        'exposure': exposure,
        'importance_multiplier': 1.0,
        'intensity': colorname,
        'intensity_multiplier': 1.0    
        }

    apscolor = APSobj.Color(colorname, values=color, alpha=1.0)

    apslight = None
    if ltype == 'point':
        apslight = APSobj.PointLight(light.getName(), xforms=xforms, **light_parms)
        return apslight, apscolor
    elif ltype == 'spot':
        return 
    # anthing else is mesh light
    filename, shops = outputTesselatedGeo(light, now, mblur_parms)
    if not filename:
        sys.stderr.write("Can't save geometry from {} to {}".format(
            light.getDefaultedString('object:soppath', now, [''])[0], filename))
        return 
    # TODO: some basics geometry shader support.
    xforms  = APSmisc.get_motionblur_xforms(light, now, mblur_parms)
    return APSobj.MeshLight(light.getName(), filename, color, exposure, 
        xforms=xforms)

    return None



    # objectTransform('space:world', light, times)

    # if isGeoLight(light, wrangler, now):
    #     IFDgeo.instanceGeometry(light, now, times)

    # IFDsettings.outputObject(light, now, wrangler=wrangler)
    # IFDsettings.outputLight(wrangler, light, now)





