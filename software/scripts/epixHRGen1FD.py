#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : ePix 10ka board instance
#-----------------------------------------------------------------------------
# File       : epix10kaDAQ.py evolved from evalBoard.py
# Author     : Ryan Herbst, rherbst@slac.stanford.edu
# Modified by: Dionisio Doering
# Created    : 2016-09-29
# Last update: 2017-02-01
#-----------------------------------------------------------------------------
# Description:
# Rogue interface to ePix 10ka board
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue_example software, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import threading
import signal
import atexit
import yaml
import time
import sys
import argparse

import PyQt4.QtGui
import PyQt4.QtCore
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue.gui
import rogue.hardware.pgp
import rogue.hardware.data

import surf
import surf.axi
import surf.protocols.ssi

import ePixViewer as vi
import ePixFpga as fpga

# Set the argument parser
parser = argparse.ArgumentParser()

# Add arguments
parser.add_argument(
    "--type", 
    type     = str,
    required = True,
    help     = "define the PCIe card type (either pgp-gen3 or kcu1500)",
)  

parser.add_argument(
    "--start_gui", 
    type     = bool,
    required = False,
    default  = True,
    help     = "true to show gui",
)  

parser.add_argument(
    "--verbose", 
    type     = bool,
    required = False,
    default  = True,
    help     = "true for verbose printout",
)  

# Get the arguments
args = parser.parse_args()

# Add PGP virtual channels
if ( args.type == 'pgp-gen3' ):

    # Create the PGP interfaces for ePix hr camera
    pgpL0Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,0) # Data & cmds
    pgpL0Vc1 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,1) # Registers for ePix board
    pgpL0Vc2 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,2) # PseudoScope
    pgpL0Vc3 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,3) # Monitoring (Slow ADC)

    pgpL1Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,0) # Data (when using all four lanes it should be swapped back with L0)
    pgpL2Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',2,0) # Data
    pgpL3Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',3,0) # Data

    print("")
    print("PGP Card Version: %x" % (pgpL0Vc0.getInfo().version))
    
elif ( args.type == 'kcu1500' ):    
    
    pgpL0Vc0 = rogue.hardware.data.DataCard('/dev/datadev_0',(1*16)+0) # Data & cmds
    pgpL0Vc1 = rogue.hardware.data.DataCard('/dev/datadev_0',(1*16)+1) # Registers for ePix board
    pgpL0Vc2 = rogue.hardware.data.DataCard('/dev/datadev_0',(1*16)+2) # PseudoScope
    pgpL0Vc3 = rogue.hardware.data.DataCard('/dev/datadev_0',(1*16)+3) # Monitoring (Slow ADC)

    pgpL1Vc0 = rogue.hardware.data.DataCard('/dev/datadev_0',(0*16)+0) # Data (when using all four lanes it should be swapped back with L0)
    pgpL2Vc0 = rogue.hardware.data.DataCard('/dev/datadev_0',(2*16)+0) # Data
    pgpL3Vc0 = rogue.hardware.data.DataCard('/dev/datadev_0',(3*16)+0) # Data    
    
else:
    raise ValueError("Invalid type (%s)" % (args.type) )

# Add data stream to file as channel 1 File writer
dataWriter = pyrogue.utilities.fileio.StreamWriter(name='dataWriter')
pyrogue.streamConnect(pgpL0Vc0, dataWriter.getChannel(0x1))

cmd = rogue.protocols.srp.Cmd()
pyrogue.streamConnect(cmd, pgpL0Vc0)

# Create and Connect SRP to VC1 to send commands
srp = rogue.protocols.srp.SrpV3()
pyrogue.streamConnectBiDir(pgpL0Vc1,srp)

#############################################
# Microblaze console printout
#############################################
class MbDebug(rogue.interfaces.stream.Slave):

    def __init__(self):
        rogue.interfaces.stream.Slave.__init__(self)
        self.enable = False

    def _acceptFrame(self,frame):
        if self.enable:
            p = bytearray(frame.getPayload())
            frame.read(p,0)
            print('-------- Microblaze Console --------')
            print(p.decode('utf-8'))

#######################################
# Custom run control
#######################################
class MyRunControl(pyrogue.RunControl):
    def __init__(self,name):
        pyrogue.RunControl.__init__(self,name, description='Run Controller ePix HR empty',  rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'})
        self._thread = None

    def _setRunState(self,dev,var,value,changed):
        if changed: 
            if self.runState.get(read=False) == 'Running': 
                self._thread = threading.Thread(target=self._run) 
                self._thread.start() 
            else: 
                self._thread.join() 
                self._thread = None 


    def _run(self):
        self.runCount.set(0) 
        self._last = int(time.time()) 
 
 
        while (self.runState.value() == 'Running'): 
            delay = 1.0 / ({value: key for key,value in self.runRate.enum.items()}[self._runRate]) 
            time.sleep(delay) 
            self._root.ssiPrbsTx.oneShot() 
  
            self._runCount += 1 
            if self._last != int(time.time()): 
                self._last = int(time.time()) 
                self.runCount._updated() 
                
##############################
# Set base
##############################
class EpixBoard(pyrogue.Root):
    def __init__(self, guiTop, cmd, dataWriter, srp, **kwargs):
        super().__init__(name='ePixHRGen1',description='ePix HR No ASIC', **kwargs)
        #self.add(MyRunControl('runControl'))
        self.add(dataWriter)
        self.guiTop = guiTop

        @self.command()
        def Trigger():
            cmd.sendCmd(0, 0)

        # Add Devices
        self.add(fpga.EpixHRGen1FD(name='EpixHRGen1', offset=0, memBase=srp, hidden=False, enabled=True))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller ePix HR Gen1 No ASIC', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))
        
# debug
mbcon = MbDebug()
pyrogue.streamTap(pgpL0Vc0,mbcon)
#pyrogue.streamTap(pgpL1Vc0,mbcon)
#pyrogue.streamTap(pgpL2Vc0,mbcon)
#pyrogue.streamTap(pgpL3Vc0,mbcon)

mbcon1 = MbDebug()
pyrogue.streamTap(pgpL1Vc0,mbcon1)

mbcon2 = MbDebug()
pyrogue.streamTap(pgpL2Vc0,mbcon2)

mbcon3 = MbDebug()
pyrogue.streamTap(pgpL3Vc0,mbcon3)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 0[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL0Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 1[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL1Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 2[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL2Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 3[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL3Vc0, dbgData)

# Create GUI
appTop = PyQt4.QtGui.QApplication(sys.argv)
guiTop = pyrogue.gui.GuiTop(group='ePixHRGEn1Gui')
ePixBoard = EpixBoard(guiTop, cmd, dataWriter, srp)
ePixBoard.start(pollEn=False, pyroGroup=None, pyroHost=None)
guiTop.addTree(ePixBoard)
guiTop.resize(800,800)

# Create GUI
if (args.start_gui):
    appTop.exec_()

# Close window and stop polling
def stop():
    mNode.stop()
    ePixBoard.stop()
    exit()

# Start with: ipython -i scripts/epix10kaDAQ.py for interactive approach
print("Started rogue mesh and epics V3 server. To exit type stop()")

