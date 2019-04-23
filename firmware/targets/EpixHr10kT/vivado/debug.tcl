##############################################################################
## This file is part of 'EPIX Development Firmware'.
## It is subject to the license terms in the LICENSE.txt file found in the 
## top-level directory of this distribution and at: 
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
## No part of 'EPIX Development Firmware', including this file, 
## may be copied, modified, propagated, or distributed except according to 
## the terms contained in the LICENSE.txt file.
##############################################################################
## User Debug Script

##############################
# Get variables and procedures
##############################
source -quiet $::env(RUCKUS_DIR)/vivado_env_var.tcl
source -quiet $::env(RUCKUS_DIR)/vivado_proc.tcl

############################
## Open the synthesis design
############################
open_run synth_1

###############################
## Set the name of the ILA core
###############################
set ilaName u_ila_1

##################
## Create the core
##################
CreateDebugCore ${ilaName}

#######################
## Set the record depth
#######################
set_property C_DATA_DEPTH 2048 [get_debug_cores ${ilaName}]

#################################
## Set the clock for the ILA core
#################################
#SetDebugCoreClk ${ilaName} {U_App/asicRdClk}
#SetDebugCoreClk ${ilaName} {U_App/appClk}
#SetDebugCoreClk ${ilaName} {U_App/sysClk}
#SetDebugCoreClk ${ilaName} {U_Core/U_DdrMem/ddrClk}
#SetDebugCoreClk ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/adcBitClkRD4}
#SetDebugCoreClk ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/adcBitClkIo}
SetDebugCoreClk ${ilaName} {U_App/byteClk}

#######################
## Set the debug Probes
#######################
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/rstL}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/coreRst[*]}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrRst}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrCalDone}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrDqsP_i[*]}
#
#ConfigProbe ${ilaName} {U_App/startDdrTest_n}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/rLite[*]}
#
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[done]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[error]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[wErrResp]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[rErrResp]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[rErrData]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[wTimerEn]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[rTimerEn]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[wTimer][*]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[rTimer][*]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[len][*]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[address][*]}
#ConfigProbe ${ilaName} {U_App/U_AxiMemTester/r[state][*]}
#
# DAC probes
#ConfigProbe ${ilaName} {U_App/WFDacDin_i}
#ConfigProbe ${ilaName} {U_App/WFDacSclk_i}
#ConfigProbe ${ilaName} {U_App/WFDacCsL_i}
#ConfigProbe ${ilaName} {U_App/WFDacLdacL_i}
#ConfigProbe ${ilaName} {U_App/WFDacClrL_i}
#ConfigProbe ${ilaName} {U_App/sDacDin_i}
#ConfigProbe ${ilaName} {U_App/sDacSclk_i}
#ConfigProbe ${ilaName} {U_App/sDacCsL_i[*]}
#fast adc probes
                        
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/adcFrame[*]}
# frame channel
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/U_FRAME_DESERIALIZER/adcDV4R[*]}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/U_FRAME_DESERIALIZER/adcDV7R[*]}
# data channel
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/GenData[0].U_DATA_DESERIALIZER/adcDV4R[*]}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/GenData[0].U_DATA_DESERIALIZER/adcDV7R[*]}
#
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/U_FRAME_DESERIALIZER/sData_i}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/U_FRAME_DESERIALIZER/loadDelaySync}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/adcBitClkRD4}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GEN_ULTRASCALE_AD9249.U_AD9249_0/adcBitClkR}


ConfigProbe ${ilaName} {U_App/iAsicAcq}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/s[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/sAxisMaster[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/imAxisMaster[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/imAxisSlave[*]}
#ConfigProbe ${ilaName} {U_App/ssiCmd_i[*]}
#ConfigProbe ${ilaName} {U_App/iDaqTrigger}
#ConfigProbe ${ilaName} {U_App/iRunTrigger}
#ConfigProbe ${ilaName} {U_App/slowAdcDin_i}
#ConfigProbe ${ilaName} {U_App/slowAdcDrdy}
#ConfigProbe ${ilaName} {U_App/slowAdcDout}
#ConfigProbe ${ilaName} {U_App/slowAdcRefClk_i}
#ConfigProbe ${ilaName} {U_App/slowAdcCsL_i}
#ConfigProbe ${ilaName} {U_App/slowAdcSclk_i}

#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GenData[0].U_DATA_DESERIALIZER/adcDV4R[*]}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GenData[0].U_DATA_DESERIALIZER/adcDV7R[*]}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/GenData[0].U_DATA_DESERIALIZER/loadDelaySync}
#ConfigProbe ${ilaName} {U_App/U_MonAdcReadout/U_FRAME_DESERIALIZER/loadDelaySync}

ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/GenData[0].U_DATA_DESERIALIZER/adcDV4R[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/GenData[0].U_DATA_DESERIALIZER/adcDV5R[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/GenData[1].U_DATA_DESERIALIZER/adcDV4R[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/GenData[1].U_DATA_DESERIALIZER/adcDV5R[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/adcData[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/dataValid[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/adcR[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/tenbData[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/rxDataCs[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/rxValidCs}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/decDataOut[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/decValidOut[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/decSof[*]}
ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/s[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_AXI_ASIC/GEN_ULTRASCALE_HRADC16.U_HrADC_0/GenData[0].U_DATA_DESERIALIZER/sData_i[*]}



### Delete the last unused port
#delete_debug_port [get_debug_ports [GetCurrentProbe ${ilaName}]]

##########################
## Write the port map file
##########################
WriteDebugProbes ${ilaName} ${PROJ_DIR}/images/debug_probes.ltx


