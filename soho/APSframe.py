#Mostly copied from IFDframe
import soho
import sohog
import hou
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

    gdp = gdp.tesselate({'geo:convstyle':'div', 'geo:triangulate':False, 'tess:polysides':4})
    if not gdp:
        sys.stderr.write("Can't tesselate geometry from {} to {}".format(soppath, filename))
        return None, None

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

def outputPrincipledShader(obj, now):
    '''Don't know how to use shop clerks at the moment.'''

    def render_tuple(tuple_):
        return "[{},{},{}]".format(*tuple_)

    def select_color_source(obj, parm_name, now, condition=False, mult=1, setexpr=False):
        objects = []
        parm = "{}_texture".format(parm_name)
        texturefile = obj.parm(parm).evalAtTime(now)
        if condition and not setexpr:
            texturename = obj.path() + '/{}_texture'.format(parm_name)
            texture, instance = APSobj.DiskTexture2D(texturename, texturefile)
            color    = instance.get('name')
            objects += [texture, instance]
        elif condition:
            color = 'texture(&quot;{}&quot;, $u, $v)'.format(texturefile)
        else:
            color = obj.parmTuple(parm_name).evalAtTime(now)
            color = [c*mult for c in color]
            color = render_tuple(color)
        return color, objects


    edfname  = None
    disney   = []

    # this should be repated for every parm, but we don't bother to fully
    # support materials this way. 
    basecolor, objs = select_color_source(obj, 'basecolor', now,
        condition=obj.parm("basecolor_useTexture").evalAtTime(now), setexpr=True)
    sssinten = obj.parm("sss").evalAtTime(now)
    ssscolor, objs = select_color_source(obj, 'ssscolor', now, 
         condition=obj.parm("sss_useTexture").evalAtTime(now), setexpr=True, mult=sssinten)
    transparency = obj.parm("transparency").evalAtTime(now)
    transcolor, objs = select_color_source(obj, 'transcolor', now, 
         condition=obj.parm("transparency_useTexture").evalAtTime(now), mult=transparency)
    if transparency != 0:
        disney += objs
    else:
        transcolor = 1.0

    # this doesn't work in Appleseed
    # opaccolor= obj.parmTuple('opaccolor').evalAtTime(now)
    # normals:

    if obj.parm("baseBumpAndNormal_enable").evalAtTime(now) and \
        obj.parm("baseNormal_texture").evalAtTime(now) != "":
        texturename = obj.path() + '/{}_texture'.format('baseNormal_texture')
        texturefile = obj.parm("baseNormal_texture").evalAtTime(now)
        texture, instance = APSobj.DiskTexture2D(texturename, texturefile) 
        disney += [texture, instance]


    emitint  = obj.parm("emitint").evalAtTime(now)
    emitcol  = obj.parmTuple('emitcolor').evalAtTime(now)
    emitcolor = [c*emitint for c in emitcol]
    emitcolor = render_tuple(emitcolor)
   
    #Emission
    if not obj.parmTuple("emitcolor").isAtDefault():
        color    = APSobj.Color(obj.path() + "_emitcolor", 
            values=emitcol, alpha=1.0)
        edf      = APSobj.Edf(obj.path() + '_edf', model='diffuse_edf', 
            radiance=color.get('name'), exposure=0, radiance_multiplier=1)
        edfname = edf.get('name')
        disney +=[color, edf]

    parms = {
        "mask"           : "1",
        "base_color"     : basecolor,
        "subsurface"     : ssscolor,
        "metallic"       : obj.parm('metallic').evalAtTime(now),
        "specular"       : obj.parm('reflect').evalAtTime(now),
        "specular_tint"  : obj.parm('reflecttint').evalAtTime(now),
        "anisotropic"    : obj.parm('aniso').evalAtTime(now),
        "roughness"      : obj.parm('rough').evalAtTime(now),
        "sheen"          : obj.parm('sheen').evalAtTime(now),
        "sheen_tint"     : obj.parm('sheentint').evalAtTime(now),
        "clearcoat"      : obj.parm('coat').evalAtTime(now),
        "clearcoat_gloss": obj.parm('coatrough').evalAtTime(now),
        "folded"         : "false",
        "edf"            : edfname,
        'alpha_map'      : transcolor # buggy
        }

    disney += APSobj.DisneyMaterial(obj.path(), **parms)
    return disney



def outputMaterial(shop_path, now):
    '''Dirty way to support at least principle (disney) material.'''
    material = soho.getObject(shop_path)
    obj      = hou.node(shop_path)
    # 
    if obj.type().name().startswith('principledshader::'):
        return outputPrincipledShader(obj, now)








