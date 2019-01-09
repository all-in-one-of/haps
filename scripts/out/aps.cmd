# Default script run when a geometry object is created
# $arg1 is the name of the object to create
\set noalias = 1
if ( "$arg1" != "" ) then
    # Add default properties
    opproperty -f -F "Output"               $arg1 appleseed default_images_output
    opproperty -f -F "Extra Image Planes"   $arg1 appleseed appleseed_images_extra
    opproperty -f -F "Extra Image Planes"   $arg1 appleseed default_images_extra_post
    opproperty -f -F "Deep Output"          $arg1 appleseed default_images_deep_output
    opproperty -f -F "Cryptomatte"          $arg1 appleseed default_images_crypto_output
    opproperty -f -F "Meta Data"            $arg1 appleseed default_images_meta
    opproperty -f -F "Rendering"            $arg1 appleseed default_rendering
    opproperty -f -F "Sampling"             $arg1 appleseed default_rendering_sampling
    opproperty -f -F "Limits"               $arg1 appleseed default_rendering_limits
    opproperty -f -F "Shading"              $arg1 appleseed default_rendering_shading
    opproperty -f -F "Render"               $arg1 appleseed default_rendering_render
    opproperty -f -F "Dicing"               $arg1 appleseed default_rendering_dicing
    opproperty -f -F "Statistics"           $arg1 appleseed default_rendering_statistics
    # Now, add singleton parameters
    opproperty -f -F "Driver" $arg1 appleseed vm_inlinestorage
    opproperty -f -F "Driver" $arg1 appleseed vm_tmpsharedstorage
    opproperty -f -F "Driver" $arg1 appleseed vm_tmplocalstorage
    opproperty -f -F "Driver" $arg1 appleseed vm_binarygeometry
endif

# Node $arg1 (Driver/aps)
opexprlanguage -s hscript $arg1
opuserdata -n '___Version___' -v '' $arg1
