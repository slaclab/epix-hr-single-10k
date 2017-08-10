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
# EVAL BOARD ONLY

set_property -dict {PACKAGE_PIN H27 IOSTANDARD LVCMOS18} [get_ports userSmaP]
set_property -dict {PACKAGE_PIN G27 IOSTANDARD LVCMOS18} [get_ports userSmaN]
set_property -dict {PACKAGE_PIN P23 IOSTANDARD LVCMOS18} [get_ports {led[0]}]
set_property -dict {PACKAGE_PIN R23 IOSTANDARD LVCMOS18} [get_ports {led[1]}]
set_property -dict {PACKAGE_PIN M22 IOSTANDARD LVCMOS18} [get_ports {led[2]}]
set_property -dict {PACKAGE_PIN N22 IOSTANDARD LVCMOS18} [get_ports {led[3]}]


####################################
## Application Timing Constraints ##
####################################

##########################
## Misc. Configurations ##
##########################

