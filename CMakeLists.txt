cmake_minimum_required(VERSION 2.8.9)

project(SequenceRegistration)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/moselhy/SlicerSequenceRegistration")
set(EXTENSION_CATEGORY "Sequences")
set(EXTENSION_CONTRIBUTORS "Mohamed Moselhy (Western University), Andras Lasso (PerkLab, Queen's University), Feng Su (Western University)")
set(EXTENSION_DESCRIPTION "This extension registers 4D volume sequences for motion compensation or motion analysis.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/moselhy/SlicerSequenceRegistration/master/SequenceRegistration/Resources/Icons/SequenceRegistration.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/moselhy/SlicerSequenceRegistration/master/screenshot01.png https://raw.githubusercontent.com/moselhy/SlicerSequenceRegistration/master/screenshot02.png")
set(EXTENSION_DEPENDS "SlicerElastix")

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
