# Define target output
target: build

# Define User's version number
export EXPORT_VERSION = 1.0

# Define Vendor Name
export EXPORT_VENDOR = SLAC

# Define if we are skipping csim to reduce build time
export SKIP_CSIM = 0

# Define if we are skipping cosim to reduce build time
export SKIP_COSIM = 0

# Set ARGV, CFLAGs, LDFLAGs
export ARGV    = 
export CFLAGS  = 
export LDFLAGS = 

# Set TOP_DIR to be the base directory for which the build directory resides
export TOP_DIR  = $(abspath $(PWD)/../../..)

# Need to modify the component.xml
#export ALL_XIL_FAMILY = 1

# Use top level makefile
include $(TOP_DIR)/submodules/ruckus/system_vitis_hls.mk
