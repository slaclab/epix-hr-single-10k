# Load RUCKUS environment and library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load ruckus files
loadRuckusTcl "$::DIR_PATH/surf"
loadRuckusTcl "$::DIR_PATH/epix-hr-core"

# Load the l2si-core source code
loadSource -lib l2si_core -dir "$::DIR_PATH/l2si-core/xpm/rtl"
loadSource -lib l2si_core -dir "$::DIR_PATH/l2si-core/base/rtl"
