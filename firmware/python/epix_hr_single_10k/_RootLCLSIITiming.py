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


class RootLCLSIITiming(pr.Root):
    def __init__(self, top_level, sim, dev = '/dev/datadev_0',  **kwargs):
        super().__init__(name='ePixHr10kT',description='ePixHrGen1 board', **kwargs)

        self.top_level = top_level
        self._sim = sim
        self._dev = dev

        # Create arrays to be filled
        self.dmaStreams = [None for lane in range(3)]
        self.dmaCtrlStreams = [None for lane in range(3)]
        self.unbatchers = [rogue.protocols.batcher.SplitterV1() for lane in range(3)]
        self.dataFilter = [rogue.interfaces.stream.Filter(False, dataCh+3) for dataCh in range(3)]


        # Create the PGP interfaces for ePix hr camera
        for lane in range(3):
            self.dmaStreams[lane] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*lane)+1,1)

        # connect
        self.dmaCtrlStreams[0] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+0,1)# Registers  
        self.dmaCtrlStreams[1] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+2,1)# PseudoScope
        self.dmaCtrlStreams[2] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+3,1)# Monitoring (Slow ADC)

        
        # Add data stream to file as channel 1 File writer
        self.add(pyrogue.utilities.fileio.StreamWriter(name='dataWriter'))
        for lane in range(3):
            pyrogue.streamConnect(self.dmaStreams[lane], self.dataWriter.getChannel(0x10*lane + 0x01))


        self._cmd = rogue.protocols.srp.Cmd()
        pyrogue.streamConnect(self._cmd, self.dmaCtrlStreams[0])

        # Create and Connect SRP to VC1 to send commands
        self._srp = rogue.protocols.srp.SrpV3()
        pyrogue.streamConnectBiDir(self.dmaCtrlStreams[0],self._srp)

      
        # Create arrays to be filled
        self.dmaStream   = [None for x in range(4)]

        @self.command()
        def Trigger():
            self._cmd.sendCmd(0, 0)
        
        self.add(epixHrCore.SysReg(name='Core', memBase=self._srp, offset=0x00000000, sim=self._sim, expand=False, pgpVersion=4,numberOfLanes=3))
        self.add(fpga.EpixHR10kT(name='EpixHR', memBase=self._srp, offset=0x80000000, hidden=False, enabled=True))
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
