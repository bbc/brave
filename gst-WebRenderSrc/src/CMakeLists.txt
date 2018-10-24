include_directories(${GSTREAMER_INCLUDE_DIRS})
include_directories(${GSTREAMER_VIDEO_INCLUDE_DIRS})

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

include_directories(${CEF_INCLUDE_PATH})
include_directories(${CEF_PATH})

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Werror -Wall ")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror -stdlib=libc++ -std=c++11")

# Logical target used to link the libcef library.
ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()

set(WEBRENDERSRC_SOURCES
        gstwebrendersrc.c
        gstwebrendersrc.h
        cef_bridge.cpp
        cef_bridge.h
        cef/Browser.cpp
        cef/Browser.h
        cef/Client.cpp
        cef/Client.h
    )

add_library(webrendersrc MODULE ${WEBRENDERSRC_SOURCES})
add_executable(cefsubprocess cef_subprocess.cpp)

target_link_libraries(webrendersrc
    ${GSTREAMER_LIBRARIES}
    ${GSTREAMER_VIDEO_LIBRARIES}
    libcef_lib
    libcef_dll_wrapper
    ${CEF_STANDARD_LIBS}
    ${CEF_BINARY_DIR}
)

target_link_libraries(cefsubprocess
    libcef_lib
    libcef_dll_wrapper
)

if("${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin")
    add_custom_command(
        TARGET webrendersrc
        POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CEF_BINARY_DIR}/Chromium Embedded Framework.framework"
        "${CEF_TARGET_OUT_DIR}/Frameworks/Chromium Embedded Framework.framework"
    )

    add_custom_command(
        TARGET webrendersrc
        POST_BUILD
        COMMAND install_name_tool -change
        "@rpath/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework"
        "/usr/local/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework"
        "$<TARGET_FILE:webrendersrc>"
    )

    add_custom_command(
        TARGET cefsubprocess
        POST_BUILD
        COMMAND install_name_tool -change
        "@rpath/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework"
        "/usr/local/Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework"
        "$<TARGET_FILE:cefsubprocess>"
    )

endif()

install(
  TARGETS webrendersrc
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_GST_PLUGINS_DIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

install(
  TARGETS cefsubprocess
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_GST_PLUGINS_DIR}
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
