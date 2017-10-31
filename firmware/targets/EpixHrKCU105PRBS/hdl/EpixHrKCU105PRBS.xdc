##############################################################################
## This file is part of 'EPIX HR Firmware'.
## It is subject to the license terms in the LICENSE.txt file found in the
## top-level directory of this distribution and at:
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
## No part of 'EPIX HR Firmware', including this file,
## may be copied, modified, propagated, or distributed except according to
## the terms contained in the LICENSE.txt file.
##############################################################################
#######################
## Application Ports ##
#######################

####################################
## Application Timing Constraints ##
####################################

##########################
## Misc. Configurations ##
##########################

create_generated_clock -name appClk  [get_pins {U_App/U_CoreClockGen/MmcmGen.U_Mmcm/CLKOUT0}]
create_generated_clock -name asicClk [get_pins {U_App/U_CoreClockGen/MmcmGen.U_Mmcm/CLKOUT1}]

set_clock_groups -asynchronous -group [get_clocks {sysClk}] -group [get_clocks {appClk}]
set_clock_groups -asynchronous -group [get_clocks {sysClk}] -group [get_clocks {asicClk}]

