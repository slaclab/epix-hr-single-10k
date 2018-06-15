# Load RUCKUS library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load Source Code
loadSource -dir "$::DIR_PATH/rtl/"

puts    "============================================================================="
puts    "===========================LOADING TESTBENCH================================="
puts    "============================================================================="
loadSource -sim_only -dir "$::DIR_PATH/tb/"

