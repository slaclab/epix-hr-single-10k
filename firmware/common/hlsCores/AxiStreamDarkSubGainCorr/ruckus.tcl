# Load RUCKUS library
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

# Load Source Code
loadSource    -path "$::DIR_PATH/rtl/AxiStreamDarkSubGainCorrP2Wrapper.vhd"

# Load HLS zip
if { [get_ips AxiStreamDarkSubGainCorrP2_0] eq ""  } {
   loadZipIpCore -dir "$::DIR_PATH/ip" -repo_path $::env(IP_REPO)
   create_ip -name AxiStreamDarkSubGainCorrP2 -vendor SLAC -library hls -version 1.0 -module_name AxiStreamDarkSubGainCorrP2_0
}
