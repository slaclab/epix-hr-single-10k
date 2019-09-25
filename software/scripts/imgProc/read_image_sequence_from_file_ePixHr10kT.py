#-----------------------------------------------------------------------------
# Title      : read images from file script
#-----------------------------------------------------------------------------
# File       : read_image_from_file.py
# Created    : 2017-06-19
# Last update: 2017-06-21
#-----------------------------------------------------------------------------
# Description:
# Simple image viewer that enble a local feedback from data collected using
# ePix cameras. The initial intent is to use it with stand alone systems
#
#-----------------------------------------------------------------------------
# This file is part of the ePix rogue. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the ePix rogue, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import os, sys, time


if (len(sys.argv[1])>0):
    rootFilename = sys.argv[1]
else:
    rootFilename = "/data/10kTHR/externalVoltage/125MHz/ePix10kT_clk125MHz_hsDAC_static_8000h_10fps"

for SDrstValue  in range(16):
    for SDclkValue  in range(16):
        currentFilename = rootFilename +"_SDrst_"+ str(SDrstValue)+"_SDclk_"+ str(SDclkValue)+".dat"
        command = 'python3 scripts/imgProc/read_image_from_file_ePixHr10kT.py ' + currentFilename
        print(command)
        os.system(command)
