# Copyright (c) 2016 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

# See the included README.md file for usage instructions.

cmake_minimum_required(VERSION 2.8.12.1)

# Only generate Debug and Release configuration types.
set(CMAKE_CONFIGURATION_TYPES Release Debug)

# Project name.
project(gst-WebRenderSrc)

# Use folders in the resulting project files.
set_property(GLOBAL PROPERTY OS_FOLDERS ON)
set(GST_INSTALL_BASE "${CMAKE_SOURCE_DIR}/third_party" CACHE INTERNAL "Path to the GStreamer install base")

# Specify the CEF distribution version.
set(CEF_VERSION "3.3497.1836.gb472a8d")

#Need a build of Gstreamer with WebRTC fixes
set(GST_REQUIRED 1.14.3)
set(GLIB_REQUIRED 2.58.1)

# Determine the platform.
if("${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin")
  set(CEF_PLATFORM "macosx64")
elseif("${CMAKE_SYSTEM_NAME}" STREQUAL "Linux")
  if(CMAKE_SIZEOF_VOID_P MATCHES 8)
    set(CEF_PLATFORM "linux64")
  else()
    set(CEF_PLATFORM "linux32")
  endif()
elseif("${CMAKE_SYSTEM_NAME}" STREQUAL "Windows")
  if(CMAKE_SIZEOF_VOID_P MATCHES 8)
    set(CEF_PLATFORM "windows64")
  else()
    set(CEF_PLATFORM "windows32")
  endif()
endif()

set(PROJECT_ARCH "x86_64")
set(CMAKE_BUILD_TYPE "Release")

include(GNUInstallDirs)

# Add this project's cmake/ directory to the module path.
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Download and extract the CEF binary distribution (executes DownloadCEF.cmake).
include(DownloadCEF)
include(FindPkgConfig)
DownloadCEF("${CEF_PLATFORM}" "${CEF_VERSION}" "${CMAKE_SOURCE_DIR}/third_party/cef")

# Add the CEF binary distribution's cmake/ directory to the module path.
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CEF_ROOT}/cmake")

# Load the CEF configuration (executes FindCEF.cmake).
find_package(CEF REQUIRED)

# find GStreamer packages
pkg_check_modules(GSTREAMER REQUIRED gstreamer-1.0>=${GST_REQUIRED})
pkg_check_modules(GSTREAMER_BASE REQUIRED gstreamer-base-1.0>=${GST_REQUIRED})
pkg_check_modules(GSTREAMER_VIDEO REQUIRED gstreamer-video-1.0>=${GST_REQUIRED})

#Find getText
find_package(Gettext REQUIRED)

set(CMAKE_INSTALL_GST_PLUGINS_DIR ${CMAKE_INSTALL_LIBDIR}/gstreamer-1.0)

# Include the libcef_dll_wrapper target (executes libcef_dll/CMakeLists.txt).
add_subdirectory(${CEF_LIBCEF_DLL_WRAPPER_PATH} libcef_dll_wrapper)

include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

message(STATUS "Compiling : ${PROJECT_NAME}-${PROJECT_VERSION}")

add_subdirectory(src)
