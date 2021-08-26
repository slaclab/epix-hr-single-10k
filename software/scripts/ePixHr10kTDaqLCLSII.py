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
import setupLibPaths
import pyrogue as pr
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue.interfaces.simulation
import pyrogue.gui
import rogue.hardware.pgp
import rogue.protocols
import pyrogue.pydm
import surf
import surf.axi
import surf.protocols.ssi
import epix_hr_core as epixHr


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
    default  = 'False',
    help     = "true to show gui",
)  

parser.add_argument(
    "--verbose", 
    type     = str,
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
# string to boolean
if (args.verbose == 'False'):
    args.verbose = False
else:
    args.verbose = True

if (args.type == 'SIM'):
    pollEn = False
    timeout = 5.0
else:
    pollEn = True
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

#######################################
# Custom run control
#######################################
class MyRunControl(pr.RunControl):
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
class Board(pr.Root):
    def __init__(self,
                 args,
                 guiTop,
                 dev    = '/dev/datadev_0',
                 dataVc = 1,
                 simPort = 11000,
                 **kwargs):
        super().__init__(name='ePixHr10kT',description='ePixHrGen1 board', **kwargs)
        self.args = args
        self.guiTop = guiTop
        self._sim = (args.type == 'SIM');
        self.simPort = simPort

        # Create arrays to be filled
        self.dmaStreams = [None for lane in range(4)]
        self.dmaCtrlStreams = [None for lane in range(3)]
        self._dbg       = [DataDebug(name='DataDebug',enPrint=False) for lane in range(4)]
        self.unbatchers = [rogue.protocols.batcher.SplitterV1() for lane in range(4)]
        self.dataFilter = [rogue.interfaces.stream.Filter(False, dataCh+3) for dataCh in range(4)]

        
        # Add PGP virtual channels
        if ( self.args.type == 'kcu1500' ):
            # Connect the streams
            for lane in range(4):
                self.dmaStreams[lane] = rogue.hardware.axi.AxiStreamDma(dev,(0x100*lane)+dataVc,1)
                self.dmaStreams[lane] >> self.unbatchers[lane] >> self._dbg[lane]
            # connect
            self.dmaCtrlStreams[0] = rogue.hardware.axi.AxiStreamDma(dev,(0x100*0)+0,1)# Registers  
            self.dmaCtrlStreams[1] = rogue.hardware.axi.AxiStreamDma(dev,(0x100*0)+2,1)# PseudoScope
            self.dmaCtrlStreams[2] = rogue.hardware.axi.AxiStreamDma(dev,(0x100*0)+3,1)# Monitoring (Slow ADC)
             

        elif ( self.args.type == 'SIM' ):          
            print('Sim mode')
            
            rogue.Logging.setFilter('pyrogue.SrpV3', rogue.Logging.Debug)
            # Connect the streams
            for lane in range(4):
                self.dmaStreams[lane] = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*lane)+2*1) # VC1
                self.dmaStreams[lane] >> self.unbatchers[lane] >> self._dbg[lane]
            # connect
            self.dmaCtrlStreams[0] = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*0) # VC0, Registers  
            self.dmaCtrlStreams[1] = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*2) # VC2, PseudoScope
            self.dmaCtrlStreams[2] = rogue.interfaces.stream.TcpClient('localhost',args.tcpPort+(34*0)+2*3) # VC3, Monitoring (Slow ADC)
   
        else:
            raise ValueError("Invalid type (%s)" % (args.type) )

        # Add data stream to file as channel 1 File writer
        self.add(pyrogue.utilities.fileio.StreamWriter(name='dataWriter'))
        for lane in range(4):
            pyrogue.streamConnect(self.dmaStreams[lane], self.dataWriter.getChannel(0x10*lane + 0x01))


        self.cmd = rogue.protocols.srp.Cmd()
        if ( self.args.type != 'dataFile' ):
            pyrogue.streamConnect(self.cmd, self.dmaStreams[lane])

        # Create and Connect SRP to VC1 to send commands
        self._srp = rogue.protocols.srp.SrpV3()
        pyrogue.streamConnectBiDir(self.dmaCtrlStreams[0],self._srp)

        
        # Viewer gui
        self.onlineViewers = [None for lane in range(4)]
        for viewerNum in range(4):
            self.onlineViewers[viewerNum] = vi.Window(cameraType='ePixHr10kT', verbose=self.args.verbose)
            self.onlineViewers[viewerNum].eventReader.frameIndex = 0
            self.onlineViewers[viewerNum].setReadDelay(0)
            self.onlineViewers[viewerNum].setWindowTitle("ePix image viewer ASIC %d" % (viewerNum))
            self.onlineViewers[viewerNum].eventReader.setDataDisplayParameters(2,viewerNum)
            self.unbatchers[0]  >> self.dataFilter[viewerNum] >> self.onlineViewers[viewerNum].eventReader
            self.dmaCtrlStreams[1] >> self.onlineViewers[viewerNum].eventReaderScope
            self.dmaCtrlStreams[2] >> self.onlineViewers[viewerNum].eventReaderMonitoring

        @self.command()
        def Trigger():
            self.cmd.sendCmd(0, 0)
        
        @self.command()
        def DisplayViewer0():
            self.onlineViewers[0].show()
        @self.command()
        def DisplayViewer1():
            self.onlineViewers[1].show()
        @self.command()
        def DisplayViewer2():
            self.onlineViewers[2].show()
        @self.command()
        def DisplayViewer3():
            self.onlineViewers[3].show()

        
        if (self.args.start_viewer == 'False'):
            for viewerNum in range(4):
                self.onlineViewers[viewerNum].hide()


        # Add Devices
        if ( self.args.type == 'kcu1500' ):
            self.add(epixHr.SysReg(name='Core', memBase=self._srp, offset=0x00000000, sim=self._sim, expand=False, pgpVersion=4,))
        self.add(fpga.EpixHR10kT(name='EpixHR', memBase=self._srp, offset=0x80000000, hidden=False, enabled=True))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller hr', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))


        


# Create GUI
appTop = QApplication(sys.argv)
guiTop = pyrogue.gui.GuiTop(group='ePixHr10kT')
with Board(args, guiTop, pollEn=pollEn, timeout=timeout) as ePixHrBoard:

    if ( args.type == 'dataFile' or args.type == 'SIM'):
        print("Simulation mode does not initialize monitoring ADC")
    else:
        #configure internal ADC        
        ePixHrBoard.EpixHR.InitHSADC()
        
    pyrogue.pydm.runPyDM(
        root  = ePixHrBoard,
        sizeX = 800,
        sizeY = 800,
        )
