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
import os

top_level = os.path.realpath(__file__).split('software')[0]

pr.addLibraryPath(top_level + 'firmware/submodules/axi-pcie-core/python')
pr.addLibraryPath(top_level + 'firmware/submodules/epix-hr-core/python')
pr.addLibraryPath(top_level + 'firmware/submodules/surf/python')
pr.addLibraryPath(top_level + 'firmware/python')
pr.addLibraryPath(top_level + 'software/python')
pr.addLibraryPath(top_level + 'firmware/submodules/l2si-core/python')
pr.addLibraryPath(top_level + 'firmware/submodules/lcls-timing-core/python')
try :
    pr.addLibraryPath(top_level+'firmware/submodules/ePixViewer/python')
except :
    print("pr.addLibraryPath Import ePixViewer failed")
    pass
