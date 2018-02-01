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
        inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            axi.AxiVersion(offset=0x00000000),
            #EpixHRCoreFpgaRegisters(name="EpixHRCoreFpgaRegisters", offset=0x01000000),
            #TriggerRegisters(name="TriggerRegisters", offset=0x02000000, expand=False),
            #SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            #epix.TixelAsic(name='TixelAsic0', offset=0x04000000, enabled=False, expand=False),
            #epix.TixelAsic(name='TixelAsic1', offset=0x04400000, enabled=False, expand=False),
            #AsicDeserRegisters(name='Asic0Deserializer', offset=0x0F000000, enabled=False, expand=False),
            #AsicDeserRegisters(name='Asic1Deserializer', offset=0x10000000, enabled=False, expand=False),
            #AsicPktRegisters(name='Asic0PktRegisters', offset=0x11000000, enabled=False, expand=False),
            #AsicPktRegisters(name='Asic1PktRegisters', offset=0x12000000, enabled=False, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False)
            #analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x09000000, channels=4, enabled=False, expand=False),
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            #analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x0A001000, enabled=False, expand=False),
            #OscilloscopeRegisters(name='Oscilloscope', offset=0x0C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            #HighSpeedDacRegisters(name='High Speed DAC', offset=0x0D000000, enabled=True, expand=False, HsDacEnum = HsDacEnum),
            #surf.misc.GenericMemory(name='waveformMem', offset=0x0E000000,nelms=1024),
            #MicroblazeLog(name='MicroblazeLog', offset=0x0B000000, expand=False),
            #MMCM7Registers(name='MMCM7Registers', offset=0x0F000000, enabled=False, expand=False)
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
# PRBS Tx target
#
#######################################################

class EpixHRGen1Prbs(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
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
            sDacRegisters(           name='SlowDacs'    ,                      offset=0x8B000000, expand=False)
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
# Fake data target
#
#######################################################
class EpixHRGen1FD(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            #axi.AxiVersion(offset=0x00000000),
            #SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            #epix.TixelAsic(name='TixelAsic0', offset=0x04000000, enabled=False, expand=False),
            #epix.TixelAsic(name='TixelAsic1', offset=0x04400000, enabled=False, expand=False),
            #AsicDeserRegisters(name='Asic0Deserializer', offset=0x0F000000, enabled=False, expand=False),
            #AsicDeserRegisters(name='Asic1Deserializer', offset=0x10000000, enabled=False, expand=False),
            #AsicPktRegisters(name='Asic0PktRegisters', offset=0x11000000, enabled=False, expand=False),
            #AsicPktRegisters(name='Asic1PktRegisters', offset=0x12000000, enabled=False, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False,),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False,),
            #analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x09000000, channels=4, enabled=False, expand=False),
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            #analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x0A001000, enabled=False, expand=False),
            #OscilloscopeRegisters(name='Oscilloscope', offset=0x0C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            #HighSpeedDacRegisters(name='High Speed DAC', offset=0x0D000000, enabled=True, expand=False, HsDacEnum = HsDacEnum),
            #surf.misc.GenericMemory(name='waveformMem', offset=0x0E000000,nelms=1024),
            #MicroblazeLog(name='MicroblazeLog', offset=0x0B000000, expand=False),
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
      
      self.add(pr.Variable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base='hex',  verify = False, mode='RW'))
#      self.add(pr.Variable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
#      self.add(pr.Variable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
#      self.add(pr.Variable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
#      self.add(pr.Variable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
#      self.add(pr.Variable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
#      self.add(pr.Variable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='R0Polarity',      description='R0Polarity',        offset=0x00000100, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='R0Delay',         description='R0Delay',           offset=0x00000104, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='R0Width',         description='R0Width',           offset=0x00000108, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqPolarity',     description='AcqPolarity',         offset=0x00000118, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AcqDelay1',       description='AcqDelay',            offset=0x0000011C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqWidth1',       description='AcqWidth',            offset=0x00000120, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='EnAPattern',      description='EnAPattern',          offset=0x00000124, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='EnAShiftPattern', description='EnAShiftPattern',     offset=0x00000128, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnAPolarity',     description='EnAPolarity',         offset=0x0000012C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='EnADelay',        description='EnADelay',            offset=0x00000130, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='EnAWidth',        description='EnAWidth',            offset=0x00000134, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='ReqTriggerCnt',     description='ReqTriggerCnt',     offset=0x00000138, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='triggerCntPerCycle',description='triggerCntPerCycle',offset=0x0000013C, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnAllFrames',       description='EnAllFrames',       offset=0x00000140, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='EnSingleFrame',     description='EnSingleFrame',     offset=0x00000140, bitSize=1,  bitOffset=1, base='bool', mode='RW'))

      self.add(pr.Variable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='FastSyncPolarity',description='FastSyncPolarity',  offset=0x0000015C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='FastSyncDelay',   description='FastSyncDelay',     offset=0x00000160, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='FastSyncWidth',   description='FastSyncWidth',     offset=0x00000164, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncPolarity',    description='SyncPolarity',      offset=0x00000168, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SyncDelay',       description='SyncDelay',         offset=0x0000016C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncWidth',       description='SyncWidth',         offset=0x00000170, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000174, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x00000178, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x0000017C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000180, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SR0Delay1',       description='SR0Delay1',         offset=0x00000184, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SR0Width1',       description='SR0Width1',         offset=0x00000188, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SR0Delay2',       description='SR0Delay2',         offset=0x0000018C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SR0Width2',       description='SR0Width2',         offset=0x00000190, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='Vid',             description='Vid',               offset=0x00000194, bitSize=1,  bitOffset=0, base='uint', mode='RW'))
      
      self.add(pr.Variable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      #self.add(pr.Variable(name='AsicPowerEnable', description='AsicPowerEnable',   offset=0x0000020C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add((
         pr.Variable(name='AsicPwrEnable',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=0,  base='bool', mode='RW'),
         pr.Variable(name='AsicPwrManual',      description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=16, base='bool', mode='RW'),
         pr.Variable(name='AsicPwrManualDig',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=20, base='bool', mode='RW'),
         pr.Variable(name='AsicPwrManualAna',   description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=21, base='bool', mode='RW'),
         pr.Variable(name='AsicPwrManualIo',    description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=22, base='bool', mode='RW'),
         pr.Variable(name='AsicPwrManualFpga',  description='AsicPower', offset=0x0000020C, bitSize=1, bitOffset=23, base='bool', mode='RW')))
      self.add(pr.Variable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='VguardDacSetting',description='VguardDacSetting',  offset=0x00000214, bitSize=16, bitOffset=0, base='uint', mode='RW'))
              #pr.Variable(name='TriggerChannel',  description='Setting1',          offset=0x00000008, bitSize=4,  bitOffset=2, base='enum', mode='RW', enum=trigChEnum),
      #self.add(pr.Variable(name='Cpix2DebugSel1',  description='Cpix2DebugSel1',    offset=0x00000218, bitSize=5,  bitOffset=0, base='enum', mode='RW', enum=debugChEnum))
      #self.add(pr.Variable(name='Cpix2DebugSel2',  description='Cpix2DebugSel2',    offset=0x0000021C, bitSize=5,  bitOffset=0, base='enum', mode='RW', enum=debugChEnum))
      self.add(pr.Variable(name='SyncCnt',         description='SyncCnt',           offset=0x00000220, bitSize=32, bitOffset=0, base='uint', mode='RO'))      

#      self.add(pr.Variable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add((
         pr.Variable(name='StartupReq',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=0, base='bool', mode='RW'),
         pr.Variable(name='StartupAck',  description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=1, base='bool', mode='RO'),
         pr.Variable(name='StartupFail', description='AdcStartup', offset=0x00000304, bitSize=1, bitOffset=2, base='bool', mode='RO')))
      
     
     
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
      
      self.add(pr.Variable(name='axiEn',           description='',                  offset=0x00000000, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='trig',            description='',                  offset=0x00000000, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='oneShot',         description='',                  offset=0x00000000, bitSize=1,  bitOffset=4, base='bool', mode='RW', verify=False))
      self.add(pr.Variable(name='cntData',         description='',                  offset=0x00000000, bitSize=1,  bitOffset=5, base='bool', mode='RW'))
      self.add(pr.Variable(name='packetLength',    description='packetLength',      offset=0x00000004, bitSize=32, bitOffset=0, base='uint', mode='RW'))      
      self.add(pr.Variable(name='tDest',           description='',                  offset=0x00000008, bitSize=8,  bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='tId',             description='',                  offset=0x00000008, bitSize=8,  bitOffset=8, base='uint', mode='RW'))

      
      
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
      
      self.add(pr.Variable(name='RunTriggerEnable',description='RunTriggerEnable',  offset=0x00000000, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='RunTriggerDelay', description='RunTriggerDelay',   offset=0x00000004, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='DaqTriggerEnable',description='DaqTriggerEnable',  offset=0x00000008, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='DaqTriggerDelay', description='DaqTriggerDelay',   offset=0x0000000C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AutoRunEn',       description='AutoRunEn',         offset=0x00000010, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AutoDaqEn',       description='AutoDaqEn',         offset=0x00000014, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AutoTrigPeriod',  description='AutoTrigPeriod',    offset=0x00000018, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PgpTrigEn',       description='PgpTrigEn',         offset=0x0000001C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AcqCountReset',   description='AcqCountReset',     offset=0x00000020, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AcqCount',        description='AcqCount',          offset=0x00000024, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      
      
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
      
      self.add(pr.Variable(name='ArmReg',          description='Arm',               offset=0x00000000, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='TrigReg',         description='Trig',              offset=0x00000004, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add((
         pr.Variable(name='ScopeEnable',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=0,  base='bool', mode='RW'),
         pr.Variable(name='TriggerEdge',     description='Setting1', offset=0x00000008, bitSize=1,  bitOffset=1,  base='enum', mode='RW', enum={0:'Falling', 1:'Rising'}),
         pr.Variable(name='TriggerChannel',  description='Setting1', offset=0x00000008, bitSize=4,  bitOffset=2,  base='enum', mode='RW', enum=trigChEnum),
         pr.Variable(name='TriggerMode',     description='Setting1', offset=0x00000008, bitSize=2,  bitOffset=6,  base='enum', mode='RW', enum={0:'Never', 1:'ArmReg', 2:'AcqStart', 3:'Always'}),
         pr.Variable(name='TriggerAdcThresh',description='Setting1', offset=0x00000008, bitSize=16, bitOffset=16, base='uint', mode='RW')))
      self.add((
         pr.Variable(name='TriggerHoldoff',  description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=0,  base='uint', mode='RW'),
         pr.Variable(name='TriggerOffset',   description='Setting2', offset=0x0000000C, bitSize=13, bitOffset=13, base='uint', mode='RW')))
      self.add((
         pr.Variable(name='TraceLength',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=0,  base='uint', mode='RW'),
         pr.Variable(name='SkipSamples',     description='Setting3', offset=0x00000010, bitSize=13, bitOffset=13, base='uint', mode='RW')))
      self.add((
         pr.Variable(name='InputChannelA',   description='Setting4', offset=0x00000014, bitSize=5,  bitOffset=0,  base='enum', mode='RW', enum=inChaEnum),
         pr.Variable(name='InputChannelB',   description='Setting4', offset=0x00000014, bitSize=5,  bitOffset=5,  base='enum', mode='RW', enum=inChbEnum)))
      self.add(pr.Variable(name='TriggerDelay',    description='TriggerDelay',      offset=0x00000018, bitSize=13, bitOffset=0, base='uint', mode='RW'))
      
      
      
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
         pr.Variable(name='enabled',         description='Enable waveform generation',                  offset=0x00000000, bitSize=1,   bitOffset=0,   base='bool', mode='RW'),
         pr.Variable(name='run',             description='Generates waveform when true',                offset=0x00000000, bitSize=1,   bitOffset=1,   base='bool', mode='RW'),
         pr.Variable(name='samplingCounter', description='Sampling period (>269, times 1/clock ref. 156MHz)', offset=0x00000004, bitSize=12,   bitOffset=0,   base='hex', mode='RW'),
         pr.Variable(name='DacValue',        description='Set a fixed value for the DAC',               offset=0x00000008, bitSize=16,  bitOffset=0,   base='hex', mode='RW'),
         pr.Variable(name='DacChannel',      description='Select the DAC channel to use',               offset=0x00000008, bitSize=2,   bitOffset=16,  base='enum', mode='RW', enum=HsDacEnum)))
      
      
      
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
         pr.Variable(name='DigitalEn',      description='Enable asic digital supply',                offset=0x00000000, bitSize=1,   bitOffset=0,   base='bool', mode='RW'),
         pr.Variable(name='AnalogEn',       description='Enable asic analog supply',                 offset=0x00000000, bitSize=1,   bitOffset=1,   base='bool', mode='RW')))
      
      
      
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
         pr.Variable(name='dac_0'  ,         description='',                  offset=0x00000000, bitSize=32,   bitOffset=0,   base='uint', mode='WO'),
         pr.Variable(name='dac_1'  ,         description='',                  offset=0x00000004, bitSize=32,   bitOffset=0,   base='uint', mode='WO'),
         pr.Variable(name='dac_2'  ,         description='',                  offset=0x00000008, bitSize=32,   bitOffset=0,   base='uint', mode='WO'),
         pr.Variable(name='dac_3'  ,         description='',                  offset=0x0000000C, bitSize=32,   bitOffset=0,   base='uint', mode='WO'),
         pr.Variable(name='dac_4'  ,         description='',                  offset=0x00000010, bitSize=32,   bitOffset=0,   base='uint', mode='WO'))
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
      
      self.add(pr.Variable(name='StreamEn',        description='StreamEn',          offset=0x00000000, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='StreamPeriod',    description='StreamPeriod',      offset=0x00000004, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AdcData0',        description='RawAdcData',        offset=0x00000040, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData1',        description='RawAdcData',        offset=0x00000044, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData2',        description='RawAdcData',        offset=0x00000048, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData3',        description='RawAdcData',        offset=0x0000004C, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData4',        description='RawAdcData',        offset=0x00000050, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData5',        description='RawAdcData',        offset=0x00000054, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData6',        description='RawAdcData',        offset=0x00000058, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData7',        description='RawAdcData',        offset=0x0000005C, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AdcData8',        description='RawAdcData',        offset=0x00000060, bitSize=24, bitOffset=0, base='hex',  mode='RO'))
      
      self.add(pr.Variable(name='EnvData0',        description='Temp1',             offset=0x00000080, bitSize=32, bitOffset=0, base='int',  mode='RO'))
      self.add(pr.Variable(name='EnvData1',        description='Temp2',             offset=0x00000084, bitSize=32, bitOffset=0, base='int',  mode='RO'))
      self.add(pr.Variable(name='EnvData2',        description='Humidity',          offset=0x00000088, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData3',        description='AsicAnalogCurr',    offset=0x0000008C, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData4',        description='AsicDigitalCurr',   offset=0x00000090, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData5',        description='AsicVguardCurr',    offset=0x00000094, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData6',        description='Unused',            offset=0x00000098, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData7',        description='AnalogVin',         offset=0x0000009C, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EnvData8',        description='DigitalVin',        offset=0x000000A0, bitSize=32, bitOffset=0, base='uint', mode='RO'))
      
      
      
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
         pr.Variable(name='CLKOUT0PhaseMux',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0HighTime',  description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0LowTime',   description='CLKOUT0Reg1', offset=0x0000008*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT0Frac',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=3, bitOffset=12, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0FracEn',    description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=11, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0Edge',      description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0NoCount',   description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT0DelayTime', description='CLKOUT0Reg2', offset=0x0000009*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT1PhaseMux',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT1HighTime',  description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT1LowTime',   description='CLKOUT1Reg1', offset=0x000000A*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT1Edge',      description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT1NoCount',   description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT1DelayTime', description='CLKOUT1Reg2', offset=0x000000B*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT2PhaseMux',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT2HighTime',  description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT2LowTime',   description='CLKOUT2Reg1', offset=0x000000C*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT2Edge',      description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT2NoCount',   description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT2DelayTime', description='CLKOUT2Reg2', offset=0x000000D*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT3PhaseMux',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT3HighTime',  description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT3LowTime',   description='CLKOUT3Reg1', offset=0x000000E*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT3Edge',      description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT3NoCount',   description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT3DelayTime', description='CLKOUT3Reg2', offset=0x000000F*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT4PhaseMux',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT4HighTime',  description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT4LowTime',   description='CLKOUT4Reg1', offset=0x0000010*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT4Edge',      description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT4NoCount',   description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT4DelayTime', description='CLKOUT4Reg2', offset=0x0000011*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT5PhaseMux',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT5HighTime',  description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT5LowTime',   description='CLKOUT5Reg1', offset=0x0000006*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT5Edge',      description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT5NoCount',   description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT5DelayTime', description='CLKOUT5Reg2', offset=0x0000007*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT6PhaseMux',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=3, bitOffset=13, base='uint', mode='RW'),
         pr.Variable(name='CLKOUT6HighTime',  description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT6LowTime',   description='CLKOUT6Reg1', offset=0x0000012*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      self.add((
         pr.Variable(name='CLKOUT6Edge',      description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=7,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT6NoCount',   description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=1, bitOffset=6,  base='uint', mode='RW'),
         pr.Variable(name='CLKOUT6DelayTime', description='CLKOUT6Reg2', offset=0x0000013*4, bitSize=6, bitOffset=0,  base='uint', mode='RW')))
      
      
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
      
      self.add(pr.Variable(name='Delay',        description='Delay',       offset=0x00000000, bitSize=5,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='Resync',       description='Resync',      offset=0x00000004, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='Locked',       description='Locked',      offset=0x00000008, bitSize=1,  bitOffset=0, base='bool', mode='RO'))
      self.add(pr.Variable(name='LockErrors',   description='LockErrors',  offset=0x0000000C, bitSize=16, bitOffset=0, base='uint', mode='RO'))
      
      for i in range(0, 64):
         self.add(pr.Variable(name='IserdeseOut'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000100+i*4, bitSize=10, bitOffset=0, base='hex', mode='RO'))
      
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
      
      self.add(pr.Variable(name='FrameCount',      description='FrameCount',     offset=0x00000000, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='SofErrors',       description='SofErrors',      offset=0x00000010, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='EofErrors',       description='EofErrors',      offset=0x00000014, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='OverflowErrors',  description='OverflowErrors', offset=0x00000018, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='TestMode',        description='TestMode',       offset=0x0000001C, bitSize=1,   bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='ResetCounters',   description='ResetCounters',  offset=0x00000020, bitSize=1,   bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='frameRate',       description='frameRate',      offset=0x00000024, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='frameRateMax',    description='frameRateMax',   offset=0x00000028, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='frameRateMin',    description='frameRateMin',   offset=0x0000002C, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidth',       description='bandwidth',      offset=0x00000030, bitSize=64,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidthMax',    description='bandwidthMax',   offset=0x00000038, bitSize=64,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidthMin',    description='bandwidthMin',   offset=0x00000040, bitSize=64,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='numRowFD',        description='numRow FakeData',offset=0x00000048, bitSize=32,  bitOffset=0, base='uint', mode='RW'))

      
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
      self.add(pr.Variable(name='ResetCounters',   description='ResetCounters',  offset=0x00000000, bitSize=1,   bitOffset=0, base='bool', mode='RW', verify=False))
      #
      self.add(pr.Variable(name='frameRate0',       description='frameRate',      offset=0x00000010, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMax0',    description='frameRateMax',   offset=0x00000014, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMin0',    description='frameRateMin',   offset=0x00000018, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidth0',       description='bandwidth',      offset=0x0000001C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMax0',    description='bandwidthMax',   offset=0x00000024, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMin0',    description='bandwidthMin',   offset=0x0000002C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      #
      self.add(pr.Variable(name='frameRate1',       description='frameRate',      offset=0x00000040, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMax1',    description='frameRateMax',   offset=0x00000044, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMin1',    description='frameRateMin',   offset=0x00000048, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidth1',       description='bandwidth',      offset=0x0000004C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMax1',    description='bandwidthMax',   offset=0x00000054, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMin1',    description='bandwidthMin',   offset=0x0000005C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      #
      self.add(pr.Variable(name='frameRate2',       description='frameRate',      offset=0x00000070, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMax2',    description='frameRateMax',   offset=0x00000074, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMin2',    description='frameRateMin',   offset=0x00000078, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidth2',       description='bandwidth',      offset=0x0000007C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMax2',    description='bandwidthMax',   offset=0x00000084, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMin2',    description='bandwidthMin',   offset=0x0000008C, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      #
      self.add(pr.Variable(name='frameRate3',       description='frameRate',      offset=0x000000A0, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMax3',    description='frameRateMax',   offset=0x000000A4, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='frameRateMin3',    description='frameRateMin',   offset=0x000000A8, bitSize=32,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidth3',       description='bandwidth',      offset=0x000000AC, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMax3',    description='bandwidthMax',   offset=0x000000B4, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      self.add(pr.Variable(name='bandwidthMin3',    description='bandwidthMin',   offset=0x000000BC, bitSize=64,  bitOffset=0, base='uint', mode='RO',pollInterval=1))
      
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
         pr.Variable(name='MemPointer',   description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=0,  base='hex', mode='RO'),
         pr.Variable(name='MemLength',    description='MemInfo', offset=0x00000000, bitSize=16,  bitOffset=16, base='hex', mode='RO')))
      
      self.add(pr.Variable(name='MemLow',    description='MemLow',   offset=0x01*4,    bitSize=2048*8, bitOffset=0, base='string', mode='RO'))
      self.add(pr.Variable(name='MemHigh',   description='MemHigh',  offset=0x201*4,   bitSize=2044*8, bitOffset=0, base='string', mode='RO'))
      
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


