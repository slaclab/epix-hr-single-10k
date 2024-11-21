##############################################################################
## This file is part of 'Vivado HLS Example'.
## It is subject to the license terms in the LICENSE.txt file found in the
## top-level directory of this distribution and at:
##    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
## No part of 'Vivado HLS Example', including this file,
## may be copied, modified, propagated, or distributed except according to
## the terms contained in the LICENSE.txt file.
##############################################################################
## Set default part
set_part {XCKU035-SFVA784-1-C}

## Set default clock (units of ns)
create_clock -period 5 -name clk
