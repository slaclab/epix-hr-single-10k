#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# This file is part of the 'Camera link gateway'. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the 'Camera link gateway', including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue as pr

pr.addLibraryPath('../../../firmware/submodules/axi-pcie-core/python')
pr.addLibraryPath('../../../firmware/submodules/surf/python')
#pr.addLibraryPath('../../../firmware/common/python')
pr.addLibraryPath('../../python')
