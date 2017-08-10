# Define if you want to check GIT build tagging
export GIT_BYPASS = 1

# Applications must define the 32-bitFirmware Version Number
export PRJ_VERSION = 0xA0000001

# COMMON_NAME is defined by application
export COMMON_NAME = FakeData

# Define the Microblaze source path
export SDK_SRC_PATH = $(PROJ_DIR)/../../common/$(COMMON_NAME)/src

# Define if you want to build the user Microblaze core
export BUILD_MB_CORE = 0

# Define if you want to build the DDR MIG core
export BUILD_MIG_CORE = 0

# Define if this is FSBL PROM address
export PROM_FSBL = 1

# Define if you want to remove unused source code
export REMOVE_UNUSED_CODE = 0

# Define target output
target: prom

# Define target part
export PRJ_PART = XCKU040-FFVA1156-2-E

# Use top level makefile
include ../../submodules/ruckus/system_vivado.mk
