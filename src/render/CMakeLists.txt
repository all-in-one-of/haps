#--------------------------------------------------------------------------------------------------
# Include paths.
#--------------------------------------------------------------------------------------------------

include_directories (${APPLESEED_INCLUDE_DIRS})

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

set (haps_sources 
    haps.cpp
    houdinitilecallbacks.cpp
    houdinitilecallbacks.h
    )

add_executable( haps ${haps_sources} )

link_directories( haps ${APPLESEED_LIBRARIES} )
target_link_libraries (haps
	# FIXME
	# appleseed
	${APPLESEED_LIBRARIES}/libappleseed.dylib
    ${APPLESEED_LIBRARIES}/libappleseed.shared.dylib
    ${Boost_LIBRARIES}
)

target_link_libraries( haps Houdini )

houdini_configure_target( haps )

