cmake_minimum_required(VERSION 2.8.9)

project(SequenceRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SequenceRegistration")
set(EXTENSION_CATEGORY "Registration")
set(EXTENSION_CONTRIBUTORS "Mohamed Moselhy (Western University)")
set(EXTENSION_DESCRIPTION "This will register a multi-volume sequence using Elastix or user-defined presets")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SequenceRegistration.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SequenceRegistration/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(Elastix4D)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
