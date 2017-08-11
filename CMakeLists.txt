cmake_minimum_required(VERSION 2.8.9)

project(SlicerSequenceRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/moselhy/SlicerSequenceRegistration")
set(EXTENSION_CATEGORY "Registration")
set(EXTENSION_CONTRIBUTORS "Mohamed Moselhy (Western University), Andras Lasso (PerkLab, Queen's University)")
set(EXTENSION_DESCRIPTION "This will register a multi-volume sequence using Elastix.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/moselhy/SlicerSequenceRegistration/master/SequenceRegistration/Resources/Icons/SequenceRegistration.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/moselhy/SlicerSequenceRegistration/master/screenshot.png")
set(EXTENSION_DEPENDS "Sequences SlicerElastix") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SequenceRegistration)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
