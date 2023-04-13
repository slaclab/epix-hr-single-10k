# Load RUCKUS library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load Source Code
loadSource    -path "$::DIR_PATH/rtl/AxiStreamePixHR10kDescrambleWrapper.vhd"
loadZipIpCore -dir "$::DIR_PATH/ip" -repo_path $::env(IP_REPO)
if { [get_ips AxiStreamePixHR10kDescramble_0] eq ""  } {
   create_ip -name AxiStreamePixHR10kDescramble -vendor SLAC -library hls -version 1.0 -module_name AxiStreamePixHR10kDescramble_0
}
