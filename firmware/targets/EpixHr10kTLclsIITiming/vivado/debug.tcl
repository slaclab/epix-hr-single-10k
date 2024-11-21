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
#open_run synth_1

###############################
## Set the name of the ILA core
###############################
#set ilaName u_ila_1

##################
## Create the core
##################
#CreateDebugCore ${ilaName}

#######################
## Set the record depth
#######################
#set_property C_DATA_DEPTH 4096 [get_debug_cores ${ilaName}]

#################################
## Set the clock for the ILA core
#################################
#SetDebugCoreClk ${ilaName} {U_App/asicRdClk}
#SetDebugCoreClk ${ilaName} {U_App/appClk}
#SetDebugCoreClk ${ilaName} {U_App/sysClk}
#SetDebugCoreClk ${ilaName} {U_App/deserClk}

#######################
## Set the debug Probes
#######################
#Probe for the SlowADC
#ConfigProbe ${ilaName} {U_App/U_AdcCntrl/state[*]}
#ConfigProbe ${ilaName} {U_App/U_AdcCntrl/ref_clk}
#ConfigProbe ${ilaName} {U_App/U_AdcCntrl/adcDrdy}
#ConfigProbe ${ilaName} {U_App/U_AdcCntrl/adcDin}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/rstL}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/coreRst[*]}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrRst}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrCalDone}
#ConfigProbe ${ilaName} {U_Core/U_DdrMem/ddrDqsP_i[*]}
#


#ConfigProbe ${ilaName} {U_App/iAsicAcq}
#ConfigProbe ${ilaName} {U_App/connMpsMux}
#ConfigProbe ${ilaName} {U_App/connTgMux}
#ConfigProbe ${ilaName} {U_App/deserData[0][*]}
#ConfigProbe ${ilaName} {U_App/rxLinkUp[*]}
#ConfigProbe ${ilaName} {U_App/rxValid[*]}
#ConfigProbe ${ilaName} {U_App/rxData[*]}
#ConfigProbe ${ilaName} {U_App/rxSof[*]}
#ConfigProbe ${ilaName} {U_App/rxEofe[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/r[txMaster][*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/startRdSync}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/dFifoRd[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/dFifoEof[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/dFifoSof[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/r[state][*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[0].U_Framers/dFifoValid[*]}
#
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/startRdSync}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/dFifoRd[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/dFifoEof[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/dFifoSof[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/r[state][*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/dFifoValid[*]}
#ConfigProbe ${ilaName} {U_App/G_ASICS[1].U_Framers/hlsTxMaster[*]}
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

#ConfigProbe ${ilaName} {U_App/iTriggerData[*]}


### Delete the last unused port
#delete_debug_port [get_debug_ports [GetCurrentProbe ${ilaName}]]

##########################
## Write the port map file
##########################
#WriteDebugProbes ${ilaName}

