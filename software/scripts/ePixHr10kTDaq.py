#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# Title      : ePix HR and ePix M DAQ top module
#-----------------------------------------------------------------------------
# File       : ePixHrePixMDaq.py evolved from evalBoard.py
# Created    : 2018-06-12
# Last update: 2018-06-12
#-----------------------------------------------------------------------------
# Description:
# Rogue interface to test board containig ePix HR attached directly to ePixM
#-----------------------------------------------------------------------------
# This file is part of the rogue_example software. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue_example software, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import setupLibPaths
import pyrogue as pr
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue.interfaces.simulation
import pyrogue.gui
import rogue.hardware.pgp
import rogue.protocols
import surf
import surf.axi
import surf.protocols.ssi
from XilinxKcu1500Pgp3.XilinxKcu1500Pgp3 import *

import threading
import signal
import atexit
import yaml
import time
import argparse
import sys
#import testBridge
import ePixViewer as vi
import ePixFpga as fpga


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
    "--start_gui", 
    type     = str,
    required = False,
    default  = 'True',
    help     = "true to show gui",
)  

parser.add_argument(
    "--start_viewer", 
    type     = str,
    required = False,
    default  = 'True',
    help     = "true to show gui",
)  

parser.add_argument(
    "--verbose", 
    type     = bool,
    required = False,
    default  = False,
    help     = "true for verbose printout",
)

parser.add_argument(
    "--tcpPort", 
    type     = int,
    required = False,
    default  = 13000,
    help     = "same port defined in the vhdl testbench",
)  

# Get the arguments
args = parser.parse_args()

# Add PGP virtual channels
if ( args.type == 'pgp-gen3' ):
    # Create the PGP interfaces for ePix hr camera
    pgpL0Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,0) # Data & cmds
    pgpL0Vc1 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,1) # Registers for ePix board
    pgpL0Vc2 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,2) # PseudoScope
    pgpL0Vc3 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,3) # Monitoring (Slow ADC)

    #pgpL1Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',0,0) # Data (when using all four lanes it should be swapped back with L0)
    pgpL2Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',2,0) # Data
    pgpL3Vc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',3,0) # Data

    print("")
    print("PGP Card Version: %x" % (pgpL0Vc0.getInfo().version))
    
elif ( args.type == 'kcu1500' ):
    # Create the PGP interfaces for ePix hr camera
    pgpL0Vc0 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*32)+0, True) # Data & cmds
    pgpL0Vc1 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*32)+1, True) # Registers for ePix board
    pgpL0Vc2 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*32)+2, True) # PseudoScope
    pgpL0Vc3 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*32)+3, True) # Monitoring (Slow ADC)

    #pgpL1Vc0 = rogue.hardware.data.DataCard('/dev/datadev_0',(0*32)+0) # Data (when using all four lanes it should be swapped back with L0)
    pgpL2Vc0 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(2*32)+0, True) # Data
    pgpL3Vc0 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(3*32)+0, True) # Data
elif ( args.type == 'SIM' ):          
    print('Sim mode')
    simPort = 11000
    rogue.Logging.setFilter('pyrogue.SrpV3', rogue.Logging.Debug)
    pgpL0Vc0  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*0) # VC0
    pgpL0Vc1  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*1) # VC1
    pgpL0Vc2  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*2) # VC2
    pgpL0Vc3  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*3) # VC3    
    pgpL2Vc0  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*2)+2*0) # L2VC0    
    pgpL3Vc0  = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*3)+2*0) # L3VC0
    
elif ( args.type == 'dataFile' ):
    print("Bypassing hardware.")

else:
    raise ValueError("Invalid type (%s)" % (args.type) )

# Add data stream to file as channel 1 File writer
dataWriter = pyrogue.utilities.fileio.StreamWriter(name='dataWriter')
if ( args.type != 'dataFile' ):
    pyrogue.streamConnect(pgpL0Vc0, dataWriter.getChannel(0x1))

cmd = rogue.protocols.srp.Cmd()
if ( args.type != 'dataFile' ):
    pyrogue.streamConnect(cmd, pgpL0Vc0)

# Create and Connect SRP to VC1 to send commands
srp = rogue.protocols.srp.SrpV3()
if ( args.type != 'dataFile' ):
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
class Board(pyrogue.Root):
    def __init__(self, guiTop, cmd, dataWriter, srp, **kwargs):
        super().__init__(name='ePixHr10kT',description='ePixHrGen1 board', **kwargs)
        self.add(dataWriter)
        self.guiTop = guiTop
        self.cmd = cmd

        @self.command()
        def Trigger():
            self.cmd.sendCmd(0, 0)

        # Add Devices
        if ( args.type == 'kcu1500' ):
            coreMap = rogue.hardware.axi.AxiMemMap('/dev/datadev_0')
            self.add(XilinxKcu1500Pgp3(memBase=coreMap))        
        self.add(fpga.EpixHR10kT(name='EpixHR', offset=0, memBase=srp, hidden=False, enabled=True))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller hr', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 0[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL0Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 1[{}]".format(0))
# if (args.verbose): pyrogue.streamTap(pgpL1Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 2[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL2Vc0, dbgData)

if (args.verbose): dbgData = rogue.interfaces.stream.Slave()
if (args.verbose): dbgData.setDebug(60, "DATA Verbose 3[{}]".format(0))
if (args.verbose): pyrogue.streamTap(pgpL3Vc0, dbgData)

# Create GUI
appTop = QApplication(sys.argv)
guiTop = pyrogue.gui.GuiTop(group='ePixHr10kT')
ePixHrBoard = Board(guiTop, cmd, dataWriter, srp)
if ( args.type == 'dataFile' or args.type == 'SIM' ):
    ePixHrBoard.start(pollEn=False,timeout=5.0 ,pyroGroup=None)
else:
    ePixHrBoard.start(pollEn=True, pyroGroup=None)
guiTop.addTree(ePixHrBoard)
guiTop.resize(800,800)

# Viewer gui
if (args.start_viewer == 'True'):
    onlineViewer = vi.Window(cameraType='ePixHr10kT')
    onlineViewer.eventReader.frameIndex = 0
    onlineViewer.setReadDelay(0)
    pyrogue.streamTap(pgpL0Vc0, onlineViewer.eventReader)

    if (args.type != 'dataFile'):
        pyrogue.streamTap(pgpL0Vc2, onlineViewer.eventReaderScope)# PseudoScope
        pyrogue.streamTap(pgpL0Vc3, onlineViewer.eventReaderMonitoring) # Slow Monitoring

if ( args.type == 'dataFile' or args.type == 'SIM'):
    print("Simulation mode does not initialize monitoring ADC")
else:
    #configure internal ADC
    ePixHrBoard.EpixHR.FastADCsDebug.enable.set(True)   
    ePixHrBoard.EpixHR.FastADCsDebug.DelayAdc0.set(15)
    ePixHrBoard.EpixHR.FastADCsDebug.enable.set(False)

    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.enable.set(True)
    ePixHrBoard.readBlocks()
    ePixHrBoard.EpixHR.FastADCsDebug.DelayAdc0.set(15)
    ePixHrBoard.EpixHR.FastADCsDebug.enable.set(False)

    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.enable.set(True)
    ePixHrBoard.readBlocks()
    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.InternalPdwnMode.set(3)
    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.InternalPdwnMode.set(0)
    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.OutputFormat.set(0)
    ePixHrBoard.readBlocks()
    ePixHrBoard.EpixHR.Ad9249Config_Adc_0.enable.set(False)
    ePixHrBoard.readBlocks()

# Create GUI
if (args.start_gui=='True'):
    appTop.exec_()

# Close window and stop polling
ePixHrBoard.stop()
exit()

