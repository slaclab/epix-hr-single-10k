#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : PyRogue AXI Version Module
#-----------------------------------------------------------------------------
# File       : 
# Author     : Maciej Kwiatkowski
# Created    : 2016-09-29
# Last update: 2017-01-31
#-----------------------------------------------------------------------------
# Description:
# PyRogue AXI Version Module for ePix100a
# for genDAQ compatibility check software/deviceLib/Epix100aAsic.cpp
#-----------------------------------------------------------------------------
# This file is part of the rogue software platform. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue software platform, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue as pr
import collections
import os
import ePixAsics as epix
import surf.axi as axi
import surf.protocols.pgp as pgp
import surf.devices.analog_devices as analog_devices
import surf.misc
import surf
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
import numpy as np

#import epix.Epix100aAsic


################################################################################################
##
## EpixHRGen1 Classes definition
##
################################################################################################
class EpixHRGenEmpty(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        inChbEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            axi.AxiVersion(offset=0x00000000),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False)
            ))

        self.add(pr.Command(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.Command(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))

    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self.waveformMem.Mem[x].set(int(waveform[x]))

            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self.waveformMem.Mem[x].get()
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')


#######################################################
#
# cryo Tx target
#
#######################################################

class EpixHRGen1Cryo(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        inChbEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A (SE)', 2:'DAC B (Diff)', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            # core registers
            axi.AxiVersion(offset=0x00000000),          
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False),
            # app registers
            MMCM7Registers(          name='MMCM7Registers',                    offset=0x80000000, enabled=False, expand=False),
            TriggerRegisters(        name="TriggerRegisters",                  offset=0x81000000, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs0PktRegisters',              offset=0x82000000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs1PktRegisters',              offset=0x82100000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs2PktRegisters',              offset=0x82200000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs3PktRegisters',              offset=0x82300000, enabled=False, expand=False),
            axi.AxiStreamMonitoring( name='AxiStreamMon',                      offset=0x82400000, numberLanes=4,enabled=False, expand=False),
            axi.AxiMemTester(        name='AxiMemTester',                      offset=0x83000000, expand=False),
            powerSupplyRegisters(    name='PowerSupply',                       offset=0x85000000, expand=False),            
            HighSpeedDacRegisters(   name='HSDac',                             offset=0x86000000, expand=False,HsDacEnum=HsDacEnum),
            #pr.MemoryDevice(         name='waveformMem',                       offset=0x8A000000, wordBitSize=16, stride=4, size=1024*4),
            sDacRegisters(           name='SlowDacs'    ,                      offset=0x86200000, enabled=False, expand=False),
            OscilloscopeRegisters(   name='Oscilloscope',                      offset=0x87000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MonAdcRegisters(         name='FastADCsDebug',                     offset=0x88000000, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]',    offset=0x88100000, enabled=False, expand=False),
            SlowAdcRegisters(        name="SlowAdcRegisters",                  offset=0x88200000, expand=False),
            DigitalPktRegisters(     name="PacketRegisters",                   offset=0x8B000000, expand=False)
            ))

        self.add(pr.Command(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.Command(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))


    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self._rawWrite(offset = (0x8A000000 + x * 4),data =  int(waveform[x]))
            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self._rawRead(offset = (0x8A000000 + x * 4))
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')



#######################################################
#
# PRBS Tx target
#
#######################################################

class EpixHRGen1Prbs(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        inChbEnum={0:'Off', 0:'Asic0TpsMux', 1:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A (SE)', 2:'DAC B (Diff)', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            # core registers
            axi.AxiVersion(offset=0x00000000),          
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False),
            #pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False),
            # app registers
            MMCM7Registers(          name='MMCM7Registers',                    offset=0x80000000, enabled=False, expand=False),
            TriggerRegisters(        name="TriggerRegisters",                  offset=0x81000000, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs0PktRegisters',              offset=0x82000000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs1PktRegisters',              offset=0x83000000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs2PktRegisters',              offset=0x84000000, enabled=False, expand=False),
            ssiPrbsTxRegisters(      name='ssiPrbs3PktRegisters',              offset=0x85000000, enabled=False, expand=False),
            axi.AxiStreamMonitoring( name='AxiStreamMon',                      offset=0x86000000, numberLanes=4,enabled=False, expand=False),
            axi.AxiMemTester(        name='AxiMemTester',                      offset=0x87000000, expand=False),
            powerSupplyRegisters(    name='PowerSupply',                       offset=0x88000000, expand=False),            
            HighSpeedDacRegisters(   name='HSDac',                             offset=0x89000000, expand=False,HsDacEnum=HsDacEnum),
            #pr.MemoryDevice(         name='waveformMem',                       offset=0x8A000000, wordBitSize=16, stride=4, size=1024*4),
            sDacRegisters(           name='SlowDacs'    ,                      offset=0x8B000000, enabled=False, expand=False),
            OscilloscopeRegisters(   name='Oscilloscope',                      offset=0x8C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MonAdcRegisters(         name='FastADCsDebug',                     offset=0x8D000000, enabled=False, expand=False),
            #analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[0]',  offset=0x8D000000, channels=4, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]',    offset=0x8E000000, enabled=False, expand=False),
            SlowAdcRegisters(        name="SlowAdcRegisters",                  offset=0x8F000000, expand=False),
            ))

        self.add(pr.Command(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.Command(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))


    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self._rawWrite(offset = (0x8A000000 + x * 4),data =  int(waveform[x]))
            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self._rawRead(offset = (0x8A000000 + x * 4))
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')






#######################################################
#
# Fake data target
#
#######################################################
class EpixHRGen1FD(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 0:'Asic0TpsMux', 0:'Asic1TpsMux'}
        inChbEnum={0:'Off', 0:'Asic0TpsMux', 0:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False,),
            MMCM7Registers(name='MMCM7Registers',                   offset=0x80000000, enabled=False, expand=False),
            EpixHRCoreFpgaRegisters(name="EpixHRCoreFpgaRegisters", offset=0x81000000),
            TriggerRegisters(name="TriggerRegisters",               offset=0x82000000, expand=False),
            AsicPktRegisters(name='Asic0PktRegisters',              offset=0x83000000, enabled=False, expand=False),
            AsicPktRegisters(name='Asic1PktRegisters',              offset=0x84000000, enabled=False, expand=False),
            AsicPktRegisters(name='Asic2PktRegisters',              offset=0x85000000, enabled=False, expand=False),
            AsicPktRegisters(name='Asic3PktRegisters',              offset=0x86000000, enabled=False, expand=False),
            axi.AxiStreamMonitoring(name='AxiStreamMon',               offset=0x87000000, enabled=False, expand=False),
            ))

        self.add(pr.Command(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.Command(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))

    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self.waveformMem.Mem[x].set(int(waveform[x]))

            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self.waveformMem.Mem[x].get()
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
      

class EpixHRCoreFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for HR Gen1 core FPGA registers"""
      super().__init__(description='HR Gen 1 core FPGA configuration registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      debugChEnum={0:'Asic01DM', 1:'AsicSync', 2:'AsicEnA', 3:'AsicAcq', 4:'AsicEnB', 5:'AsicR0', 6:'SaciClk', 7:'SaciCmd', 8:'saciRsp', 9:'SaciSelL(0)', 10:'SaciSelL(1)', 11:'asicRdClk', 12:'bitClk', 13:'byteClk', 14:'asicSR0', 15: 'acqStart'}

      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='Version',         description='Version',       offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Polarity',      description='R0Polarity',        offset=0x00000100, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Delay',         description='R0Delay',           offset=0x00000104, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='R0Width',         description='R0Width',           offset=0x00000108, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',         offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay',            offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth',            offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnAPattern',      description='EnAPattern',          offset=0x00000124, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RW'))
      self.add(pr.RemoteVariable(name='EnAShiftPattern', description='EnAShiftPattern',     offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='EnAPolarity',     description='EnAPolarity',         offset=0x0000012C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='EnADelay',        description='EnADelay',            offset=0x00000130, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='EnAWidth',        description='EnAWidth',            offset=0x00000134, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ReqTriggerCnt',     description='ReqTriggerCnt',     offset=0x00000138, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='triggerCntPerCycle',description='triggerCntPerCycle',offset=0x0000013C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnAllFrames',       description='EnAllFrames',       offset=0x00000140, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='EnSingleFrame',     description='EnSingleFrame',     offset=0x00000140, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))

      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncPolarity',description='FastSyncPolarity',  offset=0x0000015C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncDelay',   description='FastSyncDelay',     offset=0x00000160, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='FastSyncWidth',   description='FastSyncWidth',     offset=0x00000164, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x00000168, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x0000016C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x00000170, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000174, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x00000178, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x0000017C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000180, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay1',       description='SR0Delay1',         offset=0x00000184, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width1',       description='SR0Width1',         offset=0x00000188, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay2',       description='SR0Delay2',         offset=0x0000018C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width2',       description='SR0Width2',         offset=0x00000190, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='Vid',             description='Vid',               offset=0x00000194, bitSize=1,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))    
      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='AsicPwrEnable',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManual',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualDig',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualAna',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualIo',    description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualFpga',  description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='VguardDacSetting',description='VguardDacSetting',  offset=0x00000214, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncCnt',         description='SyncCnt',           offset=0x00000220, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))      
      self.add((
         pr.RemoteVariable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
     
     
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class ssiPrbsTxRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='PRBS Tx Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='axiEn',           description='',                  offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='trig',            description='',                  offset=0x00000000, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='oneShot',         description='',                  offset=0x00000000, bitSize=1,  bitOffset=4, base=pr.Bool, mode='RW', verify=False))
      self.add(pr.RemoteVariable(name='cntData',         description='',                  offset=0x00000000, bitSize=1,  bitOffset=5, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='packetLength',    description='packetLength',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))      
      self.add(pr.RemoteVariable(name='tDest',           description='',                  offset=0x00000008, bitSize=8,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='tId',             description='',                  offset=0x00000008, bitSize=8,  bitOffset=8, base=pr.UInt, disp = '{}', mode='RW'))

      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func




class TriggerRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Trigger Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='RunTriggerEnable',description='RunTriggerEnable',  offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='RunTriggerDelay', description='RunTriggerDelay',   offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='DaqTriggerEnable',description='DaqTriggerEnable',  offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='DaqTriggerDelay', description='DaqTriggerDelay',   offset=0x0000000C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AutoRunEn',       description='AutoRunEn',         offset=0x00000010, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AutoDaqEn',       description='AutoDaqEn',         offset=0x00000014, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AutoTrigPeriod',  description='AutoTrigPeriod',    offset=0x00000018, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PgpTrigEn',       description='PgpTrigEn',         offset=0x0000001C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqCountReset',   description='AcqCountReset',     offset=0x00000020, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqCount',        description='AcqCount',          offset=0x00000024, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class MonAdcRegisters(pr.Device):
   def __init__(self,  **kwargs):
      super().__init__(description='Virtual Oscilloscope Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      self.add(pr.RemoteVariable(name='DelayAdc0_', description='Data ADC Idelay3 value', offset=0x00000000, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.RemoteVariable(name='DelayAdc1_', description='Data ADC Idelay3 value', offset=0x00000004, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.RemoteVariable(name='DelayAdc2_', description='Data ADC Idelay3 value', offset=0x00000008, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.RemoteVariable(name='DelayAdc3_', description='Data ADC Idelay3 value', offset=0x0000000C, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.RemoteVariable(name='DelayAdcF_', description='Data ADC Idelay3 value', offset=0x00000020, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='DelayAdc0',      description='Data ADC Idelay3 value',       linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.DelayAdc0_]))
      self.add(pr.LinkVariable(  name='DelayAdc1',      description='Data ADC Idelay3 value',       linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.DelayAdc1_]))
      self.add(pr.LinkVariable(  name='DelayAdc2',      description='Data ADC Idelay3 value',       linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.DelayAdc2_]))
      self.add(pr.LinkVariable(  name='DelayAdc3',      description='Data ADC Idelay3 value',       linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.DelayAdc3_]))
      self.add(pr.LinkVariable(  name='DelayAdcFrame',  description='Data ADC Idelay3 value',       linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.DelayAdcF_]))

      self.add(pr.RemoteVariable(name='lockedFallCount',    description='Frame ADC Idelay3 value',              offset=0x00000030, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='lockedSync',         description='Frame ADC Idelay3 value',              offset=0x00000030, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='AdcFrameSync',       description='Frame ADC Idelay3 value',              offset=0x00000034, bitSize=14, bitOffset=0,  base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='lockedCountRst',     description='Frame ADC Idelay3 value',              offset=0x00000038, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RO'))

      self.add(pr.RemoteVariable(name='Adc0_0',             description='ADC data  value',                      offset=0x00000080, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc0_1',             description='ADC data  value',                      offset=0x00000080, bitSize=16,  bitOffset=16,base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc1_0',             description='ADC data  value',                      offset=0x00000084, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc1_1',             description='ADC data  value',                      offset=0x00000084, bitSize=16,  bitOffset=16,base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc2_0',             description='ADC data  value',                      offset=0x00000088, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc2_1',             description='ADC data  value',                      offset=0x00000088, bitSize=16,  bitOffset=16,base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc3_0',             description='ADC data  value',                      offset=0x0000008C, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      self.add(pr.RemoteVariable(name='Adc3_1',             description='ADC data  value',                      offset=0x0000008C, bitSize=16,  bitOffset=16,base=pr.UInt, disp = '{:#x}', mode='RO'))
      
      self.add(pr.RemoteVariable(name='FreezeDebug',     description='',                                        offset=0x000000A0, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RW'))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

   @staticmethod   
   def setDelay(var, value, write):
      iValue = value + 512
      var.dependencies[0].set(iValue, write)
      var.dependencies[0].set(value, write)

   @staticmethod   
   def getDelay(var, read):
      return var.dependencies[0].get(read)



      
class OscilloscopeRegisters(pr.Device):
   def __init__(self, trigChEnum, inChaEnum, inChbEnum, **kwargs):
      super().__init__(description='Virtual Oscilloscope Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='ArmReg',          description='Arm',               offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW', verify=False, pollInterval = 1))
      self.add(pr.RemoteVariable(name='TrigReg',         description='Trig',              offset=0x00000004, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW', verify=False, pollInterval = 1))
      self.add((
         pr.RemoteVariable(name='ScopeEnable',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='TriggerEdge',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=1,  mode='RW', enum={0:'Falling', 1:'Rising'}),
         pr.RemoteVariable(name='TriggerChannel',  description='Setting1', offset=0x00000008, bitSize=4,  bitOffset=2,  mode='RW', enum=trigChEnum),
         pr.RemoteVariable(name='TriggerMode',     description='Setting1', offset=0x00000008, bitSize=2,  bitOffset=6,  mode='RW', enum={0:'Never', 1:'ArmReg', 2:'AcqStart', 3:'Always'}),
         pr.RemoteVariable(name='TriggerAdcThresh',description='Setting1', offset=0x00000008, bitSize=16, bitOffset=16, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='TriggerHoldoff',  description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='TriggerOffset',   description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='TraceLength',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='SkipSamples',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='InputChannelA',   description='Setting4', offset=0x00000014, bitSize=2,  bitOffset=0,  mode='RW', enum=inChaEnum),       
         pr.RemoteVariable(name='InputChannelB',   description='Setting4', offset=0x00000014, bitSize=2,  bitOffset=5,  mode='RW', enum=inChbEnum)))
      self.add(pr.RemoteVariable(name='TriggerDelay',    description='TriggerDelay',      offset=0x00000018, bitSize=13, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class HighSpeedDacRegisters(pr.Device):
   def __init__(self, HsDacEnum, **kwargs):
      super().__init__(description='HS DAC Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add((
         pr.RemoteVariable(name='enabled',         description='Enable waveform generation',                  offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='run',             description='Generates waveform when true',                offset=0x00000000, bitSize=1,   bitOffset=1,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='samplingCounter', description='Sampling period (>269, times 1/clock ref. 156MHz)', offset=0x00000004, bitSize=12,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='DacValue',        description='Set a fixed value for the DAC',               offset=0x00000008, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='DacChannel',      description='Select the DAC channel to use',               offset=0x00000008, bitSize=2,   bitOffset=16,  mode='RW', enum=HsDacEnum)))
      
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

class powerSupplyRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Power Supply Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add((
         pr.RemoteVariable(name='DigitalEn',      description='Enable asic digital supply',                offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AnalogEn',       description='Enable asic analog supply',                 offset=0x00000000, bitSize=1,   bitOffset=1,   base=pr.Bool, mode='RW')))
      
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

class sDacRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Slow DAC Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add((
         pr.RemoteVariable(name='dac_0'  ,         description='',                  offset=0x00000000, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='dac_1'  ,         description='',                  offset=0x00000004, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='dac_2'  ,         description='',                  offset=0x00000008, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='dac_3'  ,         description='',                  offset=0x0000000C, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='dac_4'  ,         description='',                  offset=0x00000010, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'))
               )
      
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class SlowAdcRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Monitoring Slow ADC Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='StreamEn',        description='StreamEn',          offset=0x00000000, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StreamPeriod',    description='StreamPeriod',      offset=0x00000004, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AdcData0',        description='RawAdcData',        offset=0x00000040, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData1',        description='RawAdcData',        offset=0x00000044, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData2',        description='RawAdcData',        offset=0x00000048, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData3',        description='RawAdcData',        offset=0x0000004C, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData4',        description='RawAdcData',        offset=0x00000050, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData5',        description='RawAdcData',        offset=0x00000054, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData6',        description='RawAdcData',        offset=0x00000058, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData7',        description='RawAdcData',        offset=0x0000005C, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='AdcData8',        description='RawAdcData',        offset=0x00000060, bitSize=24, bitOffset=0, base=pr.UInt, disp = '{:#x}',  mode='RO'))
      
      self.add(pr.RemoteVariable(name='EnvData0',        description='Temp1',             offset=0x00000080, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}',  mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData1',        description='Temp2',             offset=0x00000084, bitSize=32, bitOffset=0, base=pr.Int,  mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData2',        description='Humidity',          offset=0x00000088, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData3',        description='AsicAnalogCurr',    offset=0x0000008C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData4',        description='AsicDigitalCurr',   offset=0x00000090, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData5',        description='AsicVguardCurr',    offset=0x00000094, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData6',        description='Unused',            offset=0x00000098, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData7',        description='AnalogVin',         offset=0x0000009C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EnvData8',        description='DigitalVin',        offset=0x000000A0, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class MMCM7Registers(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='7 Series MMCM Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add((
         pr.RemoteVariable(name='CLKOUT0PhaseMux',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0HighTime',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0LowTime',   description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT0Frac',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=3, bitOffset=12, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0FracEn',    description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=11, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0Edge',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0NoCount',   description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT0DelayTime', description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT1PhaseMux',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1HighTime',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1LowTime',   description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT1Edge',      description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1NoCount',   description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT1DelayTime', description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT2PhaseMux',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2HighTime',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2LowTime',   description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT2Edge',      description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2NoCount',   description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT2DelayTime', description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT3PhaseMux',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3HighTime',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3LowTime',   description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT3Edge',      description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3NoCount',   description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT3DelayTime', description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT4PhaseMux',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4HighTime',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4LowTime',   description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT4Edge',      description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4NoCount',   description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT4DelayTime', description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT5PhaseMux',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5HighTime',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5LowTime',   description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT5Edge',      description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5NoCount',   description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT5DelayTime', description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT6PhaseMux',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=3, bitOffset=13, base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6HighTime',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6LowTime',   description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      self.add((
         pr.RemoteVariable(name='CLKOUT6Edge',      description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=7,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6NoCount',   description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=6,  base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='CLKOUT6DelayTime', description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=6, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW')))
      
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func



class AsicDeserRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='7 Series 20 bit Deserializer Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='Delay',        description='Delay',       offset=0x00000000, bitSize=5,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',      offset=0x00000004, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='Locked',       description='Locked',      offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors',   description='LockErrors',  offset=0x0000000C, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      
      for i in range(0, 64):
         self.add(pr.RemoteVariable(name='IserdeseOut'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000100+i*4, bitSize=10, bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RO'))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class AsicPktRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',     offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',      offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',      offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors', offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestMode',        description='TestMode',       offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',  offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='frameRate',       description='frameRate',      offset=0x00000024, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='frameRateMax',    description='frameRateMax',   offset=0x00000028, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='frameRateMin',    description='frameRateMin',   offset=0x0000002C, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='bandwidth',       description='bandwidth',      offset=0x00000030, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='bandwidthMax',    description='bandwidthMax',   offset=0x00000038, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='bandwidthMin',    description='bandwidthMin',   offset=0x00000040, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='numRowFD',        description='numRow FakeData',offset=0x00000048, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))

      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

#############################################################################
## Manages Packages for cryo asic 
#############################################################################
class DigitalPktRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',     offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',      offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',      offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors', offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestMode',        description='TestMode',       offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StreamDataMode',  description='Streams data cont.',  offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StopDataTx',      description='Interrupt data stream',  offset=0x00000020, bitSize=1,   bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',  offset=0x00000024, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      



class AxiStreamMonitoring(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Axi Stream Monitoring registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables    
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',  offset=0x00000000, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW', verify=False))
      #
      self.add(pr.RemoteVariable(name='frameRate0',       description='frameRate',      offset=0x00000010, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMax0',    description='frameRateMax',   offset=0x00000014, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMin0',    description='frameRateMin',   offset=0x00000018, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidth0',       description='bandwidth',      offset=0x0000001C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMax0',    description='bandwidthMax',   offset=0x00000024, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMin0',    description='bandwidthMin',   offset=0x0000002C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      #
      self.add(pr.RemoteVariable(name='frameRate1',       description='frameRate',      offset=0x00000040, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMax1',    description='frameRateMax',   offset=0x00000044, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMin1',    description='frameRateMin',   offset=0x00000048, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidth1',       description='bandwidth',      offset=0x0000004C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMax1',    description='bandwidthMax',   offset=0x00000054, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMin1',    description='bandwidthMin',   offset=0x0000005C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      #
      self.add(pr.RemoteVariable(name='frameRate2',       description='frameRate',      offset=0x00000070, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMax2',    description='frameRateMax',   offset=0x00000074, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMin2',    description='frameRateMin',   offset=0x00000078, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidth2',       description='bandwidth',      offset=0x0000007C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMax2',    description='bandwidthMax',   offset=0x00000084, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMin2',    description='bandwidthMin',   offset=0x0000008C, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      #
      self.add(pr.RemoteVariable(name='frameRate3',       description='frameRate',      offset=0x000000A0, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMax3',    description='frameRateMax',   offset=0x000000A4, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='frameRateMin3',    description='frameRateMin',   offset=0x000000A8, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidth3',       description='bandwidth',      offset=0x000000AC, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMax3',    description='bandwidthMax',   offset=0x000000B4, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      self.add(pr.RemoteVariable(name='bandwidthMin3',    description='bandwidthMin',   offset=0x000000BC, bitSize=64,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO',pollInterval=1))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

class MicroblazeLog(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Microblaze log buffer', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add((
         pr.RemoteVariable(name='MemPointer',   description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=0,  base=pr.UInt, disp = '{:#x}', mode='RO'),
         pr.RemoteVariable(name='MemLength',    description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=16, base=pr.UInt, disp = '{:#x}', mode='RO')))
      
      self.add(pr.RemoteVariable(name='MemLow',    description='MemLow',   offset=0x01*4,    bitSize=2048*8, bitOffset=0, base='string', mode='RO'))
      self.add(pr.RemoteVariable(name='MemHigh',   description='MemHigh',  offset=0x201*4,   bitSize=2044*8, bitOffset=0, base='string', mode='RO'))
      
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


