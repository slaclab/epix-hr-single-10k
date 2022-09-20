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
import epix_hr_single_10k as epixHrRoot
import epix_hr_core as epixHrCore


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


class Root(pr.Root):
    def __init__(self, top_level, sim, asicVersion, **kwargs):
        super().__init__(name='ePixHr10kT',description='ePixHrGen1 board', **kwargs)

        self.top_level = top_level
        self._sim = sim
        self._asicVersion = asicVersion

        # Create the PGP interfaces for ePix hr camera
        self.pgpL0Vc0 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*256)+0, True) # Registers  
        self.pgpL0Vc1 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*256)+1, True) # Data & cmds
        self.pgpL0Vc2 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*256)+2, True) # PseudoScope
        self.pgpL0Vc3 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(0*256)+3, True) # Monitoring (Slow ADC)
        self.pgpL1Vc1 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(1*256)+1, True) # Data
        self.pgpL2Vc1 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(2*256)+1, True) # Data
        self.pgpL3Vc1 = rogue.hardware.axi.AxiStreamDma('/dev/datadev_0',(3*256)+1, True) # Data

        # Add data stream to file as channel 1 File writer
        self.dataWriter = pyrogue.utilities.fileio.StreamWriter(name='dataWriter')
        pyrogue.streamConnect(self.pgpL0Vc1, self.dataWriter.getChannel(0x01))
        pyrogue.streamConnect(self.pgpL1Vc1, self.dataWriter.getChannel(0x11))
        pyrogue.streamConnect(self.pgpL2Vc1, self.dataWriter.getChannel(0x21))
        pyrogue.streamConnect(self.pgpL3Vc1, self.dataWriter.getChannel(0x31))

        self._cmd = rogue.protocols.srp.Cmd()
        pyrogue.streamConnect(self._cmd, self.pgpL0Vc1)

        # Create and Connect SRP to VC1 to send commands
        self._srp = rogue.protocols.srp.SrpV3()
        pyrogue.streamConnectBiDir(self.pgpL0Vc0,self._srp)
      
        # Create arrays to be filled
        self.dmaStream   = [None for x in range(4)]
        # Connect PGP[VC=1] to SRPv3

        @self.command()
        def Trigger():
            self.cmd.sendCmd(0, 0)
        

        self.add(epixHrCore.SysReg(name='Core', memBase=self._srp, offset=0x00000000, sim=self._sim, expand=False, pgpVersion=4,))
        self.add(fpga.EpixHR10kT(name='EpixHR', memBase=self._srp, offset=0x80000000, hidden=False, enabled=True,asicVersion=self._asicVersion))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller hr', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))


def start (self,**kwargs):
        super(Root, self).start(**kwargs)

        self.EpixHR.FastADCsDebug.enable.set(True)   
        self.EpixHR.FastADCsDebug.DelayAdc0.set(15)
        self.EpixHR.FastADCsDebug.enable.set(False)

        self.EpixHR.Ad9249Config_Adc_0.enable.set(True)
        self.readBlocks()
        self.EpixHR.FastADCsDebug.DelayAdc0.set(15)
        self.EpixHR.FastADCsDebug.enable.set(False)

        self.EpixHR.Ad9249Config_Adc_0.enable.set(True)
        self.readBlocks()
        self.EpixHR.Ad9249Config_Adc_0.InternalPdwnMode.set(3)
        self.EpixHR.Ad9249Config_Adc_0.InternalPdwnMode.set(0)
        self.EpixHR.Ad9249Config_Adc_0.OutputFormat.set(0)
        self.readBlocks()
        self.EpixHR.Ad9249Config_Adc_0.enable.set(False)
        self.readBlocks()
