cmake_minimum_required(VERSION 2.8.9)

project(SequenceRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/moselhy/SequenceRegistration")
set(EXTENSION_CATEGORY "Registration")
set(EXTENSION_CONTRIBUTORS "Mohamed Moselhy (Western University), Andras Lasso (PerkLab, Queen's University)")
set(EXTENSION_DESCRIPTION "This will register a multi-volume sequence using Elastix.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/moselhy/SequenceRegistration/master/Elastix4D/Resources/Icons/Elastix4D.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/moselhy/SequenceRegistration/master/screenshot.png")
set(EXTENSION_DEPENDS "Sequence SlicerElastix") # Specified as a space separated string, a list or 'NA' if any

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
