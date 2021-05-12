# Load RUCKUS library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load Source Code
loadSource -dir "$::DIR_PATH/rtl/"

# Load Source Code common to all ePixHr family
loadSource -dir "$::DIR_PATH/../ePixHrCommon/rtl/"


