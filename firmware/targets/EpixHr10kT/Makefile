# Define if you want to check GIT build tagging
export GIT_BYPASS = 1


# COMM_TYPE is defined by application
export COMM_TYPE = pgp4
export INCLUDE_PGP4_6G = 1
# COMM_TYPE is defined by application
#export COMM_TYPE = pgp3
#export INCLUDE_PGP3_10G = 1

# COMMON_NAME is defined by application
export COMMON_NAME = ePixHr10kT

# Define the Microblaze source path
#export SDK_SRC_PATH = $(PROJ_DIR)/../../common/$(COMMON_NAME)/src

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
export PRJ_PART = XCKU035-SFVA784-1-C

# Use top level makefile
include ../shared_config.mk
include ../../submodules/ruckus/system_vivado.mk

