# Specify the minimum required version of CMake to build the project.
cmake_minimum_required( VERSION 3.4 )
project( GEOappleseedTranslator )

list( APPEND CMAKE_PREFIX_PATH "$ENV{HT}/cmake")
find_package( Houdini REQUIRED )

OPTION(BINARYMESH_VERSION_4 "BINARYMESH_VERSION_4" ON)
OPTION(BINARYMESH_VERSION_3 "BINARYMESH_VERSION_3" ON)
OPTION(BINARYMESH_VERSION_1 "BINARYMESH_VERSION_1" ON)

if(BINARYMESH_VERSION_4 OR BINARYMESH_VERSION_3)
    set(BUILD_WITH_COMPRESSION TRUE)
endif()
# lz4 if you will
set( LZ4_SRC_PATH "$ENV{LZ4_PATH}")

if (NOT EXISTS ${LZ4_SRC_PATH})
    message(WARNING "Without LZ4 exporter will produce binarmesh version 1")
    set(LZ4_LIB FALSE)
elseif (${BUILD_WITH_COMPRESSION})
    set(LZ4_LIB TRUE)
        message(STATUS "Building with LZ4")
endif()

if(${LZ4_LIB})
    if (BINARYMESH_VERSION_4)
        add_definitions(-DBINARYMESH_VERSION_4)
        message(STATUS "Building for BINARYMESH_VERSION_4")
    elseif (BINARYMESH_VERSION_3)
        add_definitions(-DBINARYMESH_VERSION_3)
        message(STATUS "Building for BINARYMESH_VERSION_3")
    endif()
else()
    if (${BUILD_WITH_COMPRESSION})
        message(WARNING "Options BINARYMESH_VERSION_3 or BINARYMESH_VERSION_4 are set, \
            but no LZ4 found.\n We will build with BINARYMESH_VERSION_1")
    endif()
        add_definitions(-DBINARYMESH_VERSION_1)
        message(STATUS "Building for BINARYMESH_VERSION_1")
endif()

if (${LZ4_LIB} AND ${BUILD_WITH_COMPRESSION})
    add_definitions(-DLZ4)
    set (lz4_sources
        ${LZ4_SRC_PATH}/lz4.c
        ${LZ4_SRC_PATH}/lz4.h
        ${LZ4_SRC_PATH}/lz4hc.c
        ${LZ4_SRC_PATH}/lz4hc.h
    )
    add_library( lz4 STATIC ${lz4_sources} )
    include_directories( ${LZ4_SRC_PATH} )

endif()

set( CMAKE_BUILD_TYPE Debug)

# Add a library with two source files.
set( library_name GEOappleseedTranslator )

add_library( ${library_name} SHARED
    src/GEOappleseedTranslator.cpp
    src/binarymesh.h
)

# Link against the Houdini libraries, and add required include directories and compile definitions.
target_link_libraries( ${library_name} Houdini )
target_link_libraries( ${library_name} tbb )

if (${LZ4_LIB} AND ${BUILD_WITH_COMPRESSION})
    target_link_libraries( ${library_name} lz4 )
endif()

# Configure several common target properties, such as its output directory.
houdini_configure_target( ${library_name} )


