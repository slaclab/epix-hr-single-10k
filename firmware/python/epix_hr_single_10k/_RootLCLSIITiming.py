import setupLibPaths
import pyrogue as pr
import pyrogue.utilities.prbs
import pyrogue.utilities.fileio
import pyrogue.interfaces.simulation
import rogue
import rogue.protocols
import pyrogue.pydm
import surf
import surf.axi
import surf.protocols.ssi
import epix_hr_single_10k as epixHrRoot
import epix_hr_core as epixHrCore


import subprocess
import time
import argparse
import sys
#import testBridge
import ePixFpga as fpga

try :
    from ePixViewer.asics import ePixHrDuo10kT
    from ePixViewer import EnvDataReceiver
    from ePixViewer import ScopeDataReceiver
except ImportError:
    print("Import ePixViewer failed")
    pass


rogue.Version.minVersion('6.0.0')

class Root(pr.Root):
    def __init__(self,
                 top_level,
                 sim,
                 asicVersion,
                 dev = '/dev/datadev_0',
                 simPort = 11000,
                 zmqSrvEn = True,  # Flag to include the ZMQ server
                 pollEn   = True,  # Enable automatic polling registers
                 justCtrl = False, # Enable if you only require Root for accessing AXI registers (no data)
                 **kwargs):
        super().__init__(name='ePixHr10kT',description='ePixHrGen1 board', **kwargs)

        self.top_level = top_level
        self._sim = sim
        self._dev = dev
        self._asicVersion = asicVersion
        self._tcpPort = simPort
        self._pollEn = pollEn
        self._justCtrl = justCtrl 

        print("Simulation mode :", self._sim)
        print("justCtrl mode :", self._justCtrl)

        #################################################################
        if zmqSrvEn:
            self.zmqServer = pyrogue.interfaces.ZmqServer(root=self, addr='127.0.0.1', port=0)
            self.addInterface(self.zmqServer)

        #################################################################

        # Create the PGP interfaces for ePix hr camera
        if (self._justCtrl == False) :
            # Create arrays to be filled
            self.dmaStreams     = [None for lane in range(3)]
            self.unbatchers     = [rogue.protocols.batcher.SplitterV1() for lane in range(3)]
            self.dataFilter     = [rogue.interfaces.stream.Filter(False, 2) for dataCh in range(3)]
            self.rate           = [rogue.interfaces.stream.RateDrop(True, 0.1) for lane in range(3)]

        self.dmaCtrlStreams = [None for lane in range(3)]
        self.dmaCalibStreams= [None for lane in range(2)]


        if ( self._sim == False ):
            # Create the PGP interfaces for ePix hr camera
            if (self._justCtrl == False) :
                for lane in range(3):
                    self.dmaStreams[lane] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*lane)+1,1)
                    self.add(ePixHrDuo10kT.DataReceiverEpixHrDuo10kT(name = f"DataReceiver{lane}"))
                    self.dmaStreams[lane] >> self.rate[lane] >> self.unbatchers[lane] >>  self.dataFilter[lane] >> getattr(self, f"DataReceiver{lane}")
                for vc in range(2):
                    lane = 2
                    vcOffset = 2
                    self.dmaCalibStreams[vc] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*lane)+(vc+vcOffset),1)

            # connect
            self.dmaCtrlStreams[0] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+0,1)# Registers  
            self.dmaCtrlStreams[1] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+2,1)# PseudoScope
            self.dmaCtrlStreams[2] = rogue.hardware.axi.AxiStreamDma(self._dev,(0x100*0)+3,1)# Monitoring (Slow ADC)
        else:
            if (self._justCtrl == False) :
                for lane in range(3):
                    self.dmaStreams[lane] = rogue.interfaces.stream.TcpClient('localhost',self._tcpPort+(34*lane)+2*1)
                    self.add(ePixHrDuo10kT.DataReceiverEpixHrDuo10kT(name = f"DataReceiver{lane}"))
                    self.dmaStreams[lane] >> self.rate[lane] >> self.unbatchers[lane] >>  self.dataFilter[lane] >> getattr(self, f"DataReceiver{lane}")
                for vc in range(2):
                    lane = 2
                    vcOffset = 2
                    self.dmaCalibStreams[vc] = rogue.interfaces.stream.TcpClient('localhost',self._tcpPort+(34*lane)+2*(vc+vcOffset))

            # connect
            self.dmaCtrlStreams[0] = rogue.interfaces.stream.TcpClient('localhost',self._tcpPort+(34*0)+2*0)# Registers  
            self.dmaCtrlStreams[1] = rogue.interfaces.stream.TcpClient('localhost',self._tcpPort+(34*0)+2*2)# PseudoScope
            self.dmaCtrlStreams[2] = rogue.interfaces.stream.TcpClient('localhost',self._tcpPort+(34*0)+2*3)# Monitoring (Slow ADC)

             # Create (Xilinx Virtual Cable) XVC on localhost
            #self.xvc = rogue.protocols.xilinx.Xvc( 2542 )
            #self.addProtocol( self.xvc )

            # Connect dmaStream[VC = 2] to XVC
            #self.dmaStream[2] == self.xvc

        
        # Add data stream to file as channel 1 File writer
        self.add(pyrogue.utilities.fileio.StreamWriter(name='dataWriter'))
        if (self._justCtrl == False) :        
            for lane in range(3):
                pyrogue.streamConnect(self.dmaStreams[lane], self.dataWriter.getChannel(0x10*lane + 0x01))


        self._cmd = rogue.protocols.srp.Cmd()
        pyrogue.streamConnect(self._cmd, self.dmaCtrlStreams[0])

        # Create and Connect SRP to VC1 to send commands
        self._srp = rogue.protocols.srp.SrpV3()
        pyrogue.streamConnectBiDir(self.dmaCtrlStreams[0],self._srp)

        # Create Dummy RX/TX
        self.dummyGen0 = epixHrRoot.SendCustomFrame()
        self.dummyGen1 = epixHrRoot.SendCustomFrame()

        # Connect Dummy RX/TX to DMA stream
        self.dummyGen0 == self.dmaCalibStreams[0]
        self.dummyGen1 == self.dmaCalibStreams[1]

      
        @self.command()
        def Trigger():
            self._cmd.sendCmd(0, 0)
            
        #if ( self._sim == False ):
        self.add(epixHrCore.SysReg(name='Core', memBase=self._srp, offset=0x00000000, sim=self._sim, expand=False, pgpVersion=4,numberOfLanes=3))
        self.add(fpga.EpixHR10kT(name='EpixHR', memBase=self._srp, offset=0x80000000, hidden=False, enabled=True, asicVersion=self._asicVersion))
        self.add(pyrogue.RunControl(name = 'runControl', description='Run Controller hr', cmd=self.Trigger, rates={1:'1 Hz', 2:'2 Hz', 4:'4 Hz', 8:'8 Hz', 10:'10 Hz', 30:'30 Hz', 60:'60 Hz', 120:'120 Hz'}))


        @self.command()
        def DisplayViewer0():
            subprocess.Popen(["python", self.top_level+"/../firmware/submodules/ePixViewer/python/ePixViewer/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.DataReceiver0", "image", "--title", "DataReceiver0",  "--sizeX", "384", "--serverList","localhost:{}".format(self.zmqServer.port()) ], shell=False)

        @self.command()
        def DisplayViewer1():
            subprocess.Popen(["python", self.top_level+"/../firmware/submodules/ePixViewer/python/ePixViewer/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.DataReceiver1", "image", "--title", "DataReceiver1",  "--sizeX", "384", "--serverList","localhost:{}".format(self.zmqServer.port()) ], shell=False)

        @self.command()
        def DisplayViewer2():
            subprocess.Popen(["python", self.top_level+"/../firmware/submodules/ePixViewer/python/ePixViewer/runLiveDisplay.py", "--dataReceiver", "rogue://0/root.DataReceiver2", "image", "--title", "DataReceiver2",  "--sizeX", "384", "--serverList","localhost:{}".format(self.zmqServer.port()) ], shell=False)


        @self.command()
        def SendCalibParam0():
            self.dummyGen0.SendCalibFrame()
        @self.command()
        def SendCalibParam1():
            self.dummyGen1.SendCalibFrame()

        #@self.command()
        #def SendCalibParam1():
        #    self.dummyGen1.SendCalibFrame()


def start (self,**kwargs):
        super(Root, self).start(**kwargs)

        if ( self._sim == False ):
            print("Init ADC")
            EpixHR.InitHSADC()            
        else:
            print("Simulation - ADC not started")
