############################
# SIMULATION code
############################

# Load RUCKUS environment and library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load submodules' code and constraints
loadRuckusTcl $::env(TOP_DIR)/submodules

# Load target's source code and constraints
#loadSource      -dir  "$::DIR_PATH/hdl/"
#loadConstraints -dir  "$::DIR_PATH/hdl/"

set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]

# set top moudule
set_property top {HrPlusM_full_tb} [get_filesets sim_1]
#set_property top {HrPlusM_registerControl_tb} [get_filesets sim_1]
#set_property top {HR16bGroup_encoded_data_tb} [get_filesets sim_1]