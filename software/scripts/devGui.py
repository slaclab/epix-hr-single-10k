#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : ePix HR 10kT Single for LCLSII timing tests
#-----------------------------------------------------------------------------
# File       : ePixHr10kTDaqLCLSII.py 
# Created    : 2018-06-12
# Last update: 2021-08-26
#-----------------------------------------------------------------------------
# Description:
#              ePix HR 10kT Single to be used to PCIe card that has the timing
#              receiver module (https://github.com/slaclab/lcls2-epix-hr-pcie)
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue_example software, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import os
top_level=f'{os.getcwd()}/'# point to the software folder
import setupLibPaths
import pyrogue as pr
import epix_hr_single_10k
import argparse
import rogue.protocols
import pyrogue.pydm


try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    import PyQt4.QtCore    
    import PyQt4.QtGui     


# Set the argument parser
parser = argparse.ArgumentParser()

# Convert str to bool
argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']

# Add arguments
parser.add_argument(
    "--type", 
    type     = str,
    required = False,
    default  = "kcu1500",
    help     = "define the PCIe card type (either pgp-gen3 or kcu1500)",
)

parser.add_argument(
    "--dev", 
    type     = str,
    required = False,
    default  = '/dev/datadev_0',
    help     = "define the PCIe card type (either pgp-gen3 or kcu1500)",
)

parser.add_argument(
        "--pollEn",
        type     = argBool,
        required = False,
        default  = True,
        help     = "Enable auto-polling",
    )

parser.add_argument(
    "--start_gui", 
    type     = str,
    required = False,
    default  = 'True',
    help     = "true to show gui",
)  

parser.add_argument(
    "--justCtrl", 
    type     = str,
    required = False,
    default  = 'False',
    help     = "true to include data",
)  

parser.add_argument(
    "--verbose", 
    type     = str,
    required = False,
    default  = True,
    help     = "true for verbose printout",
)

parser.add_argument(
    "--tcpPort", 
    type     = int,
    required = False,
    default  = 11000,
    help     = "same port defined in the vhdl testbench",
)

parser.add_argument(
    "--asicVersion", 
    type     = int,
    required = False,
    default  = 4,
    help     = "same port defined in the vhdl testbench",
)

parser.add_argument(
        "--guiType",
        type     = str,
        required = False,
        default  = 'PyDM',
        help     = "Sets the GUI type (PyDM or None)",
    )

# Get the arguments
args = parser.parse_args()
# string to boolean
if (args.verbose == 'False'):
    args.verbose = False
else:
    args.verbose = True

if (args.justCtrl == 'False'):
    args.justCtrl = False
else:
    args.justCtrl = True

if (args.type == 'SIM'):
    timeout = 5.0
else:
    timeout = 1.0

#this command can fill up the hard drive /var/log
#if (args.verbose): pgpL2Vc0.setDriverDebug(True)

    


#############################################
# Debug console printout
#############################################
class DataDebug(rogue.interfaces.stream.Slave):

    def __init__(self, name, enPrint):
        rogue.interfaces.stream.Slave.__init__(self)

        self.channelData = [[] for _ in range(8)]
        self.name = name
        self.enPrint = enPrint

    def _acceptFrame(self, frame):
        channel = frame.getChannel()

        if channel == 0 or channel == 1:
            if self.enPrint:
                print('-------------------------')
            #d = l2si_core.parseEventHeaderFrame(frame,self.enPrint)
            if self.enPrint:
            #    print(d)
                if channel == 1:
                    print(f"Raw data channel 1")
                    print('-------------------------')
                    print()

        if channel == 2:
            frameSize = frame.getPayload()
            ba = bytearray(frameSize)
            frame.read(ba, 0)
            if self.enPrint:
                print(f"Raw timing data channel 2 - {len(ba)} bytes")
                print(frame.getNumpy(0, frameSize))
                print('-------------------------')

        if channel == 3:
            frameSize = frame.getPayload()
            ba = bytearray(frameSize)
            frame.read(ba, 0)
            if self.enPrint:
                print(f"Raw camera data channel 3- {len(ba)} bytes")
                print(frame.getNumpy(0, frameSize))
                print('-------------------------')            
            
        if self.enPrint:
            print()

# Create GUI
with epix_hr_single_10k.Root(
        top_level=top_level,
        sim=False,
        asicVersion = 4,
        dev=args.dev,
        pollEn=args.pollEn,
        justCtrl = args.justCtrl,
        timeout=timeout
        ) as ePixHrBoard:

    if ( args.type == 'dataFile' or args.type == 'SIM'):
        print("Simulation mode does not initialize monitoring ADC")
    
    ######################
    # Development PyDM GUI
    ######################
    if (args.guiType == 'PyDM'):
        pyrogue.pydm.runPyDM(
            serverList = ePixHrBoard.zmqServer.address,
            sizeX      = 800,
            sizeY      = 800,
        )
