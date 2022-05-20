############################
# DO NOT EDIT THE CODE BELOW
############################

# Load RUCKUS environment and library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load submodules' code and constraints
loadRuckusTcl $::env(TOP_DIR)/submodules
loadRuckusTcl $::env(TOP_DIR)/common/$::env(COMMON_NAME)

# Load target's source code and constraints
loadSource      -dir  "$::DIR_PATH/hdl/"
loadConstraints -dir  "$::DIR_PATH/hdl/"

loadSource -sim_only -dir "$::DIR_PATH/tb/"
#set_property top {cryo_full_tb} [get_filesets sim_1]
set_property top {ePixHr10kT_full_tb} [get_filesets sim_1]
