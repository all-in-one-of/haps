######################################################
# display

add_library(houdini_ipr_display SHARED display.cpp)
target_link_libraries(houdini_ipr_display ${APPLESEED_LIBRARIES})
