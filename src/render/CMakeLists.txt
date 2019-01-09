#--------------------------------------------------------------------------------------------------
# CMake configuration.
#--------------------------------------------------------------------------------------------------

# cmake_minimum_required (VERSION 2.8 FATAL_ERROR)
cmake_minimum_required( VERSION 3.4 )

project (aps)
set( APPLESEED_DIR "$ENV{APPLESEED_PATH}")
set (CMAKE_MODULE_PATH
    ${APPLESEED_DIR}/share/cmake/Modules
    ${APPLESEED_DIR}/cmake/modules
)
set ( APPLESEED_INCLUDE_DIR ${APPLESEED_DIR}/include )
set ( APPLESEED_LIBRARY ${APPLESEED_DIR}/lib/libappleseed.dylib )
#-----------------------------------------------------------------------------------------------

option (USE_EXTERNAL_OIIO   "Use external OpenImageIO library"          OFF)
option (USE_EXTERNAL_OSL    "Use external OpenShadingLanguage library"  OFF)

option (USE_STATIC_BOOST    "Use static Boost libraries"                ON)
option (USE_STATIC_OIIO     "Use static OpenImageIO libraries"          ON)
option (USE_STATIC_OSL      "Use static OpenShadingLanguage libraries"  ON)


#--------------------------------------------------------------------------------------------------
# Compile flags.
#--------------------------------------------------------------------------------------------------

if (UNIX)
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

    # Remove when C++11 support improves.
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-declarations")
endif ()


#--------------------------------------------------------------------------------------------------
# Boost libraries.
#--------------------------------------------------------------------------------------------------

set (Boost_MULTITHREADED TRUE)

if (USE_STATIC_BOOST)
    set (Boost_USE_STATIC_LIBS TRUE)
endif ()

set (BOOST_NEEDED_LIBS system)

find_package (Boost 1.55 REQUIRED ${BOOST_NEEDED_LIBS})

add_definitions (-DBOOST_FILESYSTEM_VERSION=3 -DBOOST_FILESYSTEM_NO_DEPRECATED)

if (NOT CMAKE_SYSTEM_NAME STREQUAL "Windows")
    # Workaround for undefined reference to boost::filesystem::detail::copy_file link error
    # on Linux and macOS if Boost is built in C++03 mode.
    add_definitions (-DBOOST_NO_CXX11_SCOPED_ENUMS)
endif ()

include_directories (SYSTEM ${Boost_INCLUDE_DIRS})
link_directories (${Boost_LIBRARY_DIRS})


#--------------------------------------------------------------------------------------------------
# Find external packages.
#--------------------------------------------------------------------------------------------------
list( APPEND CMAKE_PREFIX_PATH "$ENV{HT}/cmake")
find_package( Houdini REQUIRED )
find_package (Appleseed)
find_package (Imath)
find_package (OpenEXR)

if (USE_STATIC_OIIO)
    add_definitions (-DOIIO_STATIC_BUILD)
endif ()
if (USE_EXTERNAL_OIIO)
    find_package (OpenImageIO REQUIRED)
endif ()

if (USE_STATIC_OSL)
    add_definitions (-DOSL_STATIC_LIBRARY)
endif ()
if (USE_EXTERNAL_OSL)
    find_package (OSL REQUIRED)
endif ()


#--------------------------------------------------------------------------------------------------
# Include paths.
#--------------------------------------------------------------------------------------------------

include_directories (${APPLESEED_INCLUDE_DIRS})
include_directories (${IMATH_INCLUDE_DIRS})
include_directories (${OPENEXR_INCLUDE_DIRS})
include_directories (${APPLESEED_INCLUDE_DIR2})

if (USE_EXTERNAL_OIIO)
    include_directories (${OPENIMAGEIO_INCLUDE_DIRS})
else ()
    include_directories (${APPLESEED_DEPS_STAGE_DIR}/oiio-debug/include)
endif ()

if (USE_EXTERNAL_OSL)
    include_directories (${OSL_INCLUDE_DIRS})
else ()
    include_directories (${APPLESEED_DEPS_STAGE_DIR}/osl-debug/include)
endif ()


#--------------------------------------------------------------------------------------------------
# Preprocessor definitions.
#--------------------------------------------------------------------------------------------------

if (MSVC)
    add_definitions (/D "_CRT_SECURE_NO_WARNINGS")
    add_definitions (/D "_SCL_SECURE_NO_WARNINGS")
endif ()


#--------------------------------------------------------------------------------------------------
# Product.
#--------------------------------------------------------------------------------------------------
add_definitions (-DBOOST_FILESYSTEM_VERSION=3 -DBOOST_FILESYSTEM_NO_DEPRECATED)

if (NOT CMAKE_SYSTEM_NAME STREQUAL "Windows")
    # Workaround for undefined reference to boost::filesystem::detail::copy_file link error
    # on Linux and macOS if Boost is built in C++03 mode.
    add_definitions (-DBOOST_NO_CXX11_SCOPED_ENUMS)
endif ()


set ( aps_sources 
    src/aps.cpp
    src/houdinitilecallbacks.cpp
    src/houdinitilecallbacks.h
    )

add_executable( aps ${aps_sources} )
link_directories( aps ${APPLESEED_DIR}/lib )
target_link_libraries (aps
    ${APPLESEED_LIBRARIES}
    ${Boost_LIBRARIES}
    ${IMATH_LIBRARIES}
    ${OPENEXR_LIBRARIES}
)
target_link_libraries( aps Houdini )

houdini_configure_target( aps )

