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
import rogue.hardware.pgp
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue.gui
import surf
import surf.axi
import surf.protocols.ssi
import threading
import signal
import atexit
import yaml
import time
import sys
#import testBridge
import PyQt4.QtGui
import PyQt4.QtCore
import ePixViewer as vi
import ePixFpga as fpga

#############################################
# Define if the GUI is started (1 starts it)
START_GUI = True
START_VIEWER = False
#############################################
#print debug info
PRINT_VERBOSE = False
#############################################

# Create the PGP interfaces for ePix camera
pgpVc0 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,0) # Data & cmds
pgpVc1 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,1) # Registers for ePix board
pgpVc2 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,2) # PseudoScope
pgpVc3 = rogue.hardware.pgp.PgpCard('/dev/pgpcard_0',1,3) # Monitoring (Slow ADC)

print("")
print("PGP Card Version: %x" % (pgpVc0.getInfo().version))


# Add data stream to file as channel 1
# File writer
dataWriter = pyrogue.utilities.fileio.StreamWriter('dataWriter')
pyrogue.streamConnect(pgpVc0, dataWriter.getChannel(0x1))
# Add pseudoscope to file writer
#pyrogue.streamConnect(pgpVc2, dataWriter.getChannel(0x2))
#pyrogue.streamConnect(pgpVc3, dataWriter.getChannel(0x3))

cmd = rogue.protocols.srp.Cmd()
pyrogue.streamConnect(cmd, pgpVc0)

# Create and Connect SRP to VC1 to send commands
srp = rogue.protocols.srp.SrpV3()
pyrogue.streamConnectBiDir(pgpVc1,srp)

# Add configuration stream to file as channel 0
# Removed to reduce amount of data going to file
#pyrogue.streamConnect(ePixBoard,dataWriter.getChannel(0x0))

## Add microblaze console stream to file as channel 2
#pyrogue.streamConnect(pgpVc3,dataWriter.getChannel(0x2))

# PRBS Receiver as secdonary receiver for VC1
#prbsRx = pyrogue.utilities.prbs.PrbsRx('prbsRx')
#pyrogue.streamTap(pgpVc1,prbsRx)
#ePixBoard.add(prbsRx)

# Microblaze console monitor add secondary tap
#mbcon = MbDebug()
#pyrogue.streamTap(pgpVc3,mbcon)

#br = testBridge.Bridge()
#br._setSlave(srp)

#ePixBoard.add(surf.SsiPrbsTx.create(memBase=srp1,offset=0x00000000*4))

# Create epics node
#epics = pyrogue.epics.EpicsCaServer('rogueTest',ePixBoard)
#epics.start()


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
        super().__init__('ePixHRGen1','ePix HR No ASIC', pollEn=True, **kwargs)
        #self.add(MyRunControl('runControl'))
        self.add(dataWriter)
        self.guiTop = guiTop

        @self.command()
        def Trigger():
            cmd.sendCmd(0, 0)

        # Add Devices
        self.add(fpga.EpixHRGenEmpty(name='EpixHRGen1', offset=0, memBase=srp, hidden=False, enabled=True))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller ePix HR Gen1 No ASIC', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))
        

        


# debug
#mbcon = MbDebug()
#pyrogue.streamTap(pgpVc0,mbcon)

#mbcon1 = MbDebug()
#pyrogue.streamTap(pgpVc1,mbcon)

#mbcon2 = MbDebug()
#pyrogue.streamTap(pgpVc3,mbcon)

if (PRINT_VERBOSE): dbgData = rogue.interfaces.stream.Slave()
if (PRINT_VERBOSE): dbgData.setDebug(60, "DATA[{}]".format(0))
if (PRINT_VERBOSE): pyrogue.streamTap(pgpVc0, dbgData)


# Create GUI
appTop = PyQt4.QtGui.QApplication(sys.argv)
guiTop = pyrogue.gui.GuiTop('ePixHRGEn1Gui')
ePixBoard = EpixBoard(guiTop, cmd, dataWriter, srp)
ePixBoard.start(pollEn=False, pyroGroup=None, pyroHost=None)
guiTop.addTree(ePixBoard)
guiTop.resize(800,800)

# Viewer gui
#gui = vi.Window(cameraType = 'ePix10ka')
#gui.eventReader.frameIndex = 0
#gui.eventReaderImage.VIEW_DATA_CHANNEL_ID = 0
#gui.setReadDelay(0)
#pyrogue.streamTap(pgpVc0, gui.eventReader) 
#pyrogue.streamTap(pgpVc2, gui.eventReaderScope)# PseudoScope
#pyrogue.streamTap(pgpVc3, gui.eventReaderMonitoring) # Slow Monitoring

# Create mesh node (this is for remote control only, no data is shared with this)
#mNode = pyrogue.mesh.MeshNode('rogueTest',iface='eth0',root=ePixBoard)
#mNode = pyrogue.mesh.MeshNode('rogueEpix10ka',iface='eth0',root=None)
#mNode.setNewTreeCb(guiTop.addTree)
#mNode.start()


# Run gui
if (START_GUI):
    appTop.exec_()

# Close window and stop polling
def stop():
    mNode.stop()
#    epics.stop()
    ePixBoard.stop()
    exit()

# Start with: ipython -i scripts/epix10kaDAQ.py for interactive approach
print("Started rogue mesh and epics V3 server. To exit type stop()")

