export GIT_BYPASS = 1

##########################################################################################
# Applications must define the 32-bitFirmware Version Number
##########################################################################################
export PRJ_VERSION = 0x00000001

##########################################################################################
# Applications must define the application common path where AppCore.vhd exists
##########################################################################################

# COMMON_NAME is defined by application
export COMMON_NAME = Empty

# Define the Microblaze source path
export SDK_SRC_PATH = $(PROJ_DIR)/../../common/$(COMMON_NAME)/src

##########################################################################################
# Application have the option to remove unused source code from Vivado project
#     If REMOVE_UNUSED_CODE = 0, all source code is kept after importing to Vivado project
#     If REMOVE_UNUSED_CODE = 1, all unused source code is removed from Vivado project
##########################################################################################
export REMOVE_UNUSED_CODE = 0

# Define target output
target: prom

# Define target part
export PRJ_PART = XCKU035-SFVA784-1-C

# Use top level makefile
include ../../submodules/ruckus/system_vivado.mk
