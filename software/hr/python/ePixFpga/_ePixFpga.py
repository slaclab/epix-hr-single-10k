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
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False, pollEn=False)
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
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane0', offset=0x05000000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane1', offset=0x05010000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane2', offset=0x05020000, enabled=True, expand=False, pollEn=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi_lane3', offset=0x05030000, enabled=True, expand=False, pollEn=False),
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
            AxiStreamMonitoring(name='AxiStreamMon0',               offset=0x87000000, enabled=False, expand=False),
            AxiStreamMonitoring(name='AxiStreamMon1',               offset=0x87000034, enabled=False, expand=False),
            AxiStreamMonitoring(name='AxiStreamMon2',               offset=0x87000068, enabled=False, expand=False),
            AxiStreamMonitoring(name='AxiStreamMon3',               offset=0x8700009C, enabled=False, expand=False),
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


################################################################################################
##
## epix10ka Classes definition
##
################################################################################################

class HrPrototype(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR prototype FPGA"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A', 2:'DAC B', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            axi.AxiVersion(offset=0x00000000),
            TixelFpgaRegisters(name="HrPrototypeFpgaRegisters", offset=0x01000000),
            TriggerRegisters(name="TriggerRegisters", offset=0x02000000, expand=False),
            SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            epix.TixelAsic(name='TixelAsic0', offset=0x04000000, enabled=False, expand=False),
            epix.TixelAsic(name='TixelAsic1', offset=0x04400000, enabled=False, expand=False),
            AsicDeserRegisters(name='Asic0Deserializer', offset=0x0F000000, enabled=False, expand=False),
            AsicDeserRegisters(name='Asic1Deserializer', offset=0x10000000, enabled=False, expand=False),
            AsicPktRegisters(name='Asic0PktRegisters', offset=0x11000000, enabled=False, expand=False),
            AsicPktRegisters(name='Asic1PktRegisters', offset=0x12000000, enabled=False, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x06000000, enabled=False, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x09000000, channels=4, enabled=False, expand=False),
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #surf.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x0A001000, enabled=False, expand=False),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x0C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            HighSpeedDacRegisters(name='High Speed DAC', offset=0x0D000000, enabled=True, expand=False, HsDacEnum = HsDacEnum),
            surf.misc.GenericMemory(name='waveformMem', offset=0x0E000000,nelms=1024),
            MicroblazeLog(name='MicroblazeLog', offset=0x0B000000, expand=False),
            MMCM7Registers(name='MMCM7Registers', offset=0x0F000000, enabled=False, expand=False)))

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
      

class HrPrototypeFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for HR prototype"""
      super().__init__(description='HR prototype Configuration Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.Variable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='R0Polarity',      description='R0Polarity',        offset=0x00000100, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='R0Delay',         description='R0Delay',           offset=0x00000104, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='R0Width',         description='R0Width',           offset=0x00000108, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000118, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AcqDelay1',       description='AcqDelay1',         offset=0x0000011C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqWidth1',       description='AcqWidth1',         offset=0x00000120, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqDelay2',       description='AcqDelay2',         offset=0x00000124, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqWidth2',       description='AcqWidth2',         offset=0x00000128, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='TpulsePolarity',  description='TpulsePolarity',    offset=0x0000012C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='TpulseDelay',     description='TpulseDelay',       offset=0x00000130, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='TpulseWidth',     description='TpulseWidth',       offset=0x00000134, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='StartPolarity',   description='StartPolarity',     offset=0x00000138, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='StartDelay',      description='StartDelay',        offset=0x0000013C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='StartWidth',      description='StartWidth',        offset=0x00000140, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncPolarity',    description='SyncPolarity',      offset=0x0000015C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SyncDelay',       description='SyncDelay',         offset=0x00000160, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncWidth',       description='SyncWidth',         offset=0x00000164, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000168, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000016C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000170, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      
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
      self.add(pr.Variable(name='TixelDebugSel1',  description='TixelDebugSel1',    offset=0x00000218, bitSize=5,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TixelDebugSel2',  description='TixelDebugSel2',    offset=0x0000021C, bitSize=5,  bitOffset=0, base='hex',  mode='RW'))
      
      self.add(pr.Variable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base='uint', mode='RW'))
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

################################################################################################
##
## epix100a Classes definition
##
################################################################################################
class Epix100a(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIX10KA FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1', 13:'AsicSaciSel2', 14:'AsicSaciSel3'}
      #TODO: assign meaningful channel names
      inChaEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      inChbEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize variable
      addrSize = 4	
      
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            Epix100aFpgaRegisters(name="EpixFpgaRegisters", offset=0x00000000, expand=True),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x00000140, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x00300000, expand=False),
            epix.Epix100aAsic(name='Epix100aAsic0', offset=0x00800000*addrSize, hidden=False, enabled=False, expand=False),
            epix.Epix100aAsic(name='Epix100aAsic1', offset=0x00900000*addrSize, hidden=False, enabled=False, expand=False),
            epix.Epix100aAsic(name='Epix100aAsic2', offset=0x00A00000*addrSize, hidden=False, enabled=False, expand=False),
            epix.Epix100aAsic(name='Epix100aAsic3', offset=0x00B00000*addrSize, hidden=False, enabled=False, expand=False),
            axi.AxiVersion(offset=0x08000000, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[0]', offset=0x14000000, channels=8, enabled=False, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[1]', offset=0x18000000, channels=8, enabled=False, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x1C000000, channels=4, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x20000000, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x20000800, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x20001000, enabled=False, expand=False),
            MicroblazeLog(name='MicroblazeLog', offset=0x24000000, expand=False)))
      

class Epix100aFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Configuration Registers', **kwargs)
      
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize variable
      addrSize = 4	
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      self.add(pr.Variable(name='Version',             description='FPGA firmware version number',                            offset=0x00000000*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='RunTriggerEnable',    description='Enable external run trigger',                             offset=0x00000001*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='RunTriggerDelay',     description='Run trigger delay',                                       offset=0x00000002*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DaqTriggerEnable',    description='Enable external run trigger',                             offset=0x00000003*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='DaqTriggerDelay',     description='Run trigger delay',                                       offset=0x00000004*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AcqCount',            description='Acquisition counter',                                     offset=0x00000005*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Command( name='AcqCountReset',       description='Reset acquisition counter',                               offset=0x00000006*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero))
      self.add(pr.Variable(name='DacData',             description='Sets analog DAC (MAX5443)',                               offset=0x00000007*addrSize, bitSize=16, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DigitalPowerEnable',  description='Digital power enable',                                    offset=0x00000008*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AnalogPowerEnable',   description='Analog power enable',                                     offset=0x00000008*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='FpgaOutputEnable',    description='Fpga output enable',                                      offset=0x00000008*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='IDelayCtrlRdy',       description='Ready flag for IDELAYCTRL block',                         offset=0x0000000A*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='SeqCount',            description='Sequence (frame) Counter',                                offset=0x0000000B*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Command( name='SeqCountReset',       description='Reset (frame) counter',                                   offset=0x0000000C*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touch))
      self.add(pr.Variable(name='AsicMask',            description='ASIC mask bits for the SACI access',                      offset=0x0000000D*addrSize, bitSize=4,  bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='BaseClock',           description='FPGA base clock frequency',                               offset=0x00000010*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AutoRunEnable',       description='Enable auto run trigger',                                 offset=0x00000011*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AutoRunPeriod',       description='Auto run trigger period',                                 offset=0x00000012*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AutoDaqEnable',       description='Enable auto DAQ trigger',                                 offset=0x00000013*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='OutPipelineDelay',    description='Number of clock cycles to delay ASIC digital output bit', offset=0x0000001F*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AcqToAsicR0Delay',    description='Delay (in 10ns) between system acq and ASIC reset pulse', offset=0x00000020*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicR0ToAsicAcq',     description='Delay (in 10ns) between ASIC reset pulse and int. window',offset=0x00000021*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicAcqWidth',        description='Width (in 10ns) of ASIC acq signal',                      offset=0x00000022*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW')) 
      self.add(pr.Variable(name='AsicAcqLToPPmatL',    description='Delay (in 10ns) bet. ASIC acq drop and power pulse drop', offset=0x00000023*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicRoClkHalfT',      description='Width (in 10ns) of half of readout clock (10 = 5MHz)',    offset=0x00000024*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcReadsPerPixel',    description='Number of ADC samples to record for each ASIC',           offset=0x00000025*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))  
      self.add(pr.Variable(name='AdcClkHalfT',         description='Width (in 8ns) of half clock period of ADC',              offset=0x00000026*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TotalPixelsToRead',   description='Total numbers of pixels to be readout',                   offset=0x00000027*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicGR',              description='ASIC Global Reset',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicAcq',             description='ASIC Acq Signal',                                         offset=0x00000029*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicRO',              description='ASIC R0 Signal',                                          offset=0x00000029*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPpmat',           description='ASIC Ppmat Signal',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=3, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPpbe',            description='ASIC Ppbe Signal',                                        offset=0x00000029*addrSize, bitSize=1,  bitOffset=4, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicRoClk',           description='ASIC RO Clock Signal',                                    offset=0x00000029*addrSize, bitSize=1,  bitOffset=5, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinGRControl',    description='Manual ASIC Global Reset Enabled',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinAcqControl',   description='Manual ASIC Acq Enabled',                                 offset=0x0000002A*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinROControl',    description='Manual ASIC R0 Enabled',                                  offset=0x0000002A*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinPpmatControl', description='Manual ASIC Ppmat Enabled',                               offset=0x0000002A*addrSize, bitSize=1,  bitOffset=3, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinPpbeControl',  description='Manual ASIC Ppbe Enabled',                                offset=0x0000002A*addrSize, bitSize=1,  bitOffset=4, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinROClkControl', description='Manual ASIC RO Clock Enabled',                            offset=0x0000002A*addrSize, bitSize=1,  bitOffset=5, base='bool', mode='RW'))
      self.add(pr.Variable(name='AdcStreamMode',       description='Enables manual test of ADC',                              offset=0x0000002A*addrSize, bitSize=1,  bitOffset=7, base='bool', mode='RW'))
      self.add(pr.Variable(name='AdcPatternEnable',    description='Enables test pattern on data out',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=8, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicR0Mode',          description='AsicR0Mode',                                              offset=0x0000002A*addrSize, bitSize=1,  bitOffset=11,base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicR0Width',         description='Width of R0 low pulse',                                   offset=0x0000002B*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DigitalCardId0',      description='Digital Card Serial Number (low 32 bits)',                offset=0x00000030*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='DigitalCardId1',      description='Digital Card Serial Number (high 32 bits)',               offset=0x00000031*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AnalogCardId0',       description='Analog Card Serial Number (low 32 bits)',                 offset=0x00000032*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AnalogCardId1',       description='Analog Card Serial Number (high 32 bits)',                offset=0x00000033*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AsicPreAcqTime',      description='Sum of time delays leading to the ASIC ACQ pulse',        offset=0x00000039*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AsicPPmatToReadout',  description='Delay (in 10ns) between Ppmat pulse and readout',         offset=0x0000003A*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='CarrierCardId0',      description='Carrier Card Serial Number (low 32 bits)',                offset=0x0000003B*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='CarrierCardId1',      description='Carrier Card Serial Number (high 32 bits)',               offset=0x0000003C*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='PgpTrigEn',           description='Set to enable triggering over PGP. Disables the TTL trigger input', offset=0x0000003D*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='MonStreamEn',         description='Set to enable monitor data stream over PGP',              offset=0x0000003E*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='TpsTiming',           description='Delay TPS signal',                                        offset=0x00000040*addrSize, bitSize=16, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TpsEdge',             description='Sync TPS to rising or falling edge of Acq',               offset=0x00000040*addrSize, bitSize=1,  bitOffset=16,base='bool', mode='RW'))
      self.add(pr.Variable(name='RequestStartup',      description='Request startup sequence',                                offset=0x00000080*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='StartupDone',         description='Startup sequence done',                                   offset=0x00000080*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RO'))
      self.add(pr.Variable(name='StartupFail',         description='Startup sequence failed',                                 offset=0x00000080*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RO'))
      self.add(pr.Variable(name='RequestConfDump',     description='Request Conf. Dump',                                      offset=0x00000081*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='WO'))
      self.add(pr.Variable(name='AdcPipelineDelayA0',  description='Number of samples to delay ADC reads of the ASIC0 chls',  offset=0x00000090*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA1',  description='Number of samples to delay ADC reads of the ASIC1 chls',  offset=0x00000091*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA2',  description='Number of samples to delay ADC reads of the ASIC2 chls',  offset=0x00000092*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA3',  description='Number of samples to delay ADC reads of the ASIC3 chls',  offset=0x00000093*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='EnvData00',           description='Thermistor0 temperature',                                 offset=0x00000140*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData01',           description='Thermistor1 temperature',                                 offset=0x00000141*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData02',           description='Humidity',                                                offset=0x00000142*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData03',           description='ASIC analog current',                                     offset=0x00000143*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData04',           description='ASIC digital current',                                    offset=0x00000144*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData05',           description='Guard ring current',                                      offset=0x00000145*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData06',           description='Detector bias current',                                   offset=0x00000146*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData07',           description='Analog raw input voltage',                                offset=0x00000147*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData08',           description='Digital raw input voltage',                               offset=0x00000148*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))


  
      #####################################
      # Create commands
      #####################################
  
      self.add(pr.Command(name='masterReset',   description='Master Board Reset', function=pr.Command.postedTouch))
      self.add(pr.Command(name='fpgaReload',    description='Reload FPGA',        function=self.cmdFpgaReload))
      self.add(pr.Command(name='counterReset',  description='Counter Reset',      function='  self.counter.post(0)'))
      self.add(pr.Command(name='testCpsw',      description='Test CPSW',          function=collections.OrderedDict({ 'masterResetVar': 1, 'usleep': 100, 'counter': 1 })))

      # Overwrite reset calls with local functions
      #self.setResetFunc(self.resetFunc)
     

   def cmdFpgaReload(dev,cmd,arg):
      """Example command function"""
      dev.Version.post(1)
   
   def resetFunc(dev,rstType):
      """Application specific reset function"""
      if rstType == 'soft':
         print('AxiVersion countReset')
      elif rstType == 'hard':
         dev.masterResetVar.post(1)
      elif rstType == 'count':
         print('AxiVersion countReset')

   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func




################################################################################################
##
## epix10ka Classes definition
##
################################################################################################
class Epix10ka(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "EPIX10KA FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1', 13:'AsicSaciSel2', 14:'AsicSaciSel3'}
      #TODO: assign meaningful channel names
      inChaEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      inChbEnum={
            10:'ASIC0_B0',  2: 'ASIC0_B1',  1: 'ASIC0_B2',  0: 'ASIC0_B3', 
            8: 'ASIC1_B0',  9: 'ASIC1_B1',  3: 'ASIC1_B2',  4: 'ASIC1_B3', 
            5: 'ASIC2_B0',  6: 'ASIC2_B1',  7: 'ASIC2_B2',  15:'ASIC2_B3', 
            14:'ASIC3_B0',  13:'ASIC3_B1',  12:'ASIC3_B2',  11:'ASIC3_B3', 
            17:'ASIC0_TPS', 19:'ASIC1_TPS', 18:'ASIC2_TPS', 16:'ASIC3_TPS'}
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            Epix10kaFpgaRegisters(name="EpixFpgaRegisters", offset=0x00000000),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x00000140, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x00300000, expand=False),
            epix.Epix10kaAsic(name='Epix10kaAsic0', offset=0x02000000, enabled=False, expand=False),
            epix.Epix10kaAsic(name='Epix10kaAsic1', offset=0x02400000, enabled=False, expand=False),
            epix.Epix10kaAsic(name='Epix10kaAsic2', offset=0x02800000, enabled=False, expand=False),
            epix.Epix10kaAsic(name='Epix10kaAsic3', offset=0x02C00000, enabled=False, expand=False),
            axi.AxiVersion(offset=0x08000000),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[0]', offset=0x14000000, channels=8, enabled=False, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[1]', offset=0x18000000, channels=8, enabled=False, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x1C000000, channels=4, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x20000000, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x20000800, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x20001000, enabled=False, expand=False),
            MicroblazeLog(name='MicroblazeLog', offset=0x24000000, expand=False)))
      

class Epix10kaFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Epix"""
      super().__init__(description='Epix Configuration Registers', **kwargs)
      
      #In order to easely compare GedDAQ address map with the eprix rogue address map 
      #it is defined the addrSize variable
      addrSize = 4	
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      self.add(pr.Variable(name='Version',             description='FPGA firmware version number',                            offset=0x00000000*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='RunTriggerEnable',    description='Enable external run trigger',                             offset=0x00000001*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='RunTriggerDelay',     description='Run trigger delay',                                       offset=0x00000002*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DaqTriggerEnable',    description='Enable external run trigger',                             offset=0x00000003*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='DaqTriggerDelay',     description='Run trigger delay',                                       offset=0x00000004*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AcqCount',            description='Acquisition counter',                                     offset=0x00000005*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Command( name='AcqCountReset',       description='Reset acquisition counter',                               offset=0x00000006*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero))
      self.add(pr.Variable(name='DacData',             description='Sets analog DAC (MAX5443)',                               offset=0x00000007*addrSize, bitSize=16, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DigitalPowerEnable',  description='Digital power enable',                                    offset=0x00000008*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AnalogPowerEnable',   description='Analog power enable',                                     offset=0x00000008*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='FpgaOutputEnable',    description='Fpga output enable',                                      offset=0x00000008*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='IDelayCtrlRdy',       description='Ready flag for IDELAYCTRL block',                         offset=0x0000000A*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='SeqCount',            description='Sequence (frame) Counter',                                offset=0x0000000B*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Command( name='SeqCountReset',       description='Reset (frame) counter',                                   offset=0x0000000C*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touch))
      self.add(pr.Variable(name='AsicMask',            description='ASIC mask bits for the SACI access',                      offset=0x0000000D*addrSize, bitSize=4,  bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='BaseClock',           description='FPGA base clock frequency',                               offset=0x00000010*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AutoRunEnable',       description='Enable auto run trigger',                                 offset=0x00000011*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AutoRunPeriod',       description='Auto run trigger period',                                 offset=0x00000012*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AutoDaqEnable',       description='Enable auto DAQ trigger',                                 offset=0x00000013*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='OutPipelineDelay',    description='Number of clock cycles to delay ASIC digital output bit', offset=0x0000001F*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AcqToAsicR0Delay',    description='Delay (in 10ns) between system acq and ASIC reset pulse', offset=0x00000020*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicR0ToAsicAcq',     description='Delay (in 10ns) between ASIC reset pulse and int. window',offset=0x00000021*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicAcqWidth',        description='Width (in 10ns) of ASIC acq signal',                      offset=0x00000022*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW')) 
      self.add(pr.Variable(name='AsicAcqLToPPmatL',    description='Delay (in 10ns) bet. ASIC acq drop and power pulse drop', offset=0x00000023*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicRoClkHalfT',      description='Width (in 10ns) of half of readout clock (10 = 5MHz)',    offset=0x00000024*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcReadsPerPixel',    description='Number of ADC samples to record for each ASIC',           offset=0x00000025*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))  
      self.add(pr.Variable(name='AdcClkHalfT',         description='Width (in 8ns) of half clock period of ADC',              offset=0x00000026*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TotalPixelsToRead',   description='Total numbers of pixels to be readout',                   offset=0x00000027*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AsicGR',              description='ASIC Global Reset',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicAcq',             description='ASIC Acq Signal',                                         offset=0x00000029*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicRO',              description='ASIC R0 Signal',                                          offset=0x00000029*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPpmat',           description='ASIC Ppmat Signal',                                       offset=0x00000029*addrSize, bitSize=1,  bitOffset=3, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPpbe',            description='ASIC Ppbe Signal',                                        offset=0x00000029*addrSize, bitSize=1,  bitOffset=4, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicRoClk',           description='ASIC RO Clock Signal',                                    offset=0x00000029*addrSize, bitSize=1,  bitOffset=5, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinGRControl',    description='Manual ASIC Global Reset Enabled',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinAcqControl',   description='Manual ASIC Acq Enabled',                                 offset=0x0000002A*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinROControl',    description='Manual ASIC R0 Enabled',                                  offset=0x0000002A*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinPpmatControl', description='Manual ASIC Ppmat Enabled',                               offset=0x0000002A*addrSize, bitSize=1,  bitOffset=3, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinPpbeControl',  description='Manual ASIC Ppbe Enabled',                                offset=0x0000002A*addrSize, bitSize=1,  bitOffset=4, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicPinROClkControl', description='Manual ASIC RO Clock Enabled',                            offset=0x0000002A*addrSize, bitSize=1,  bitOffset=5, base='bool', mode='RW'))
      self.add(pr.Variable(name='AdcStreamMode',       description='Enables manual test of ADC',                              offset=0x0000002A*addrSize, bitSize=1,  bitOffset=7, base='bool', mode='RW'))
      self.add(pr.Variable(name='AdcPatternEnable',    description='Enables test pattern on data out',                        offset=0x0000002A*addrSize, bitSize=1,  bitOffset=8, base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicR0Mode',          description='AsicR0Mode',                                              offset=0x0000002A*addrSize, bitSize=1,  bitOffset=11,base='bool', mode='RW'))
      self.add(pr.Variable(name='AsicR0Width',         description='Width of R0 low pulse',                                   offset=0x0000002B*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='DigitalCardId0',      description='Digital Card Serial Number (low 32 bits)',                offset=0x00000030*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='DigitalCardId1',      description='Digital Card Serial Number (high 32 bits)',               offset=0x00000031*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AnalogCardId0',       description='Analog Card Serial Number (low 32 bits)',                 offset=0x00000032*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AnalogCardId1',       description='Analog Card Serial Number (high 32 bits)',                offset=0x00000033*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AsicPreAcqTime',      description='Sum of time delays leading to the ASIC ACQ pulse',        offset=0x00000039*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='AsicPPmatToReadout',  description='Delay (in 10ns) between Ppmat pulse and readout',         offset=0x0000003A*addrSize, bitSize=31, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='CarrierCardId0',      description='Carrier Card Serial Number (low 32 bits)',                offset=0x0000003B*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='CarrierCardId1',      description='Carrier Card Serial Number (high 32 bits)',               offset=0x0000003C*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='PgpTrigEn',           description='Set to enable triggering over PGP. Disables the TTL trigger input', offset=0x0000003D*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='MonStreamEn',         description='Set to enable monitor data stream over PGP',              offset=0x0000003E*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='TpsTiming',           description='Delay TPS signal',                                        offset=0x00000040*addrSize, bitSize=16, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TpsEdge',             description='Sync TPS to rising or falling edge of Acq',               offset=0x00000040*addrSize, bitSize=1,  bitOffset=16,base='bool', mode='RW'))
      self.add(pr.Variable(name='RequestStartup',      description='Request startup sequence',                                offset=0x00000080*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='StartupDone',         description='Startup sequence done',                                   offset=0x00000080*addrSize, bitSize=1,  bitOffset=1, base='bool', mode='RO'))
      self.add(pr.Variable(name='StartupFail',         description='Startup sequence failed',                                 offset=0x00000080*addrSize, bitSize=1,  bitOffset=2, base='bool', mode='RO'))
      self.add(pr.Variable(name='RequestConfDump',     description='Request Conf. Dump',                                      offset=0x00000081*addrSize, bitSize=1,  bitOffset=0, base='bool', mode='WO'))
      self.add(pr.Variable(name='AdcPipelineDelayA0',  description='Number of samples to delay ADC reads of the ASIC0 chls',  offset=0x00000090*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA1',  description='Number of samples to delay ADC reads of the ASIC1 chls',  offset=0x00000091*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA2',  description='Number of samples to delay ADC reads of the ASIC2 chls',  offset=0x00000092*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='AdcPipelineDelayA3',  description='Number of samples to delay ADC reads of the ASIC3 chls',  offset=0x00000093*addrSize, bitSize=8,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='EnvData00',           description='Thermistor0 temperature',                                 offset=0x00000140*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData01',           description='Thermistor1 temperature',                                 offset=0x00000141*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData02',           description='Humidity',                                                offset=0x00000142*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData03',           description='ASIC analog current',                                     offset=0x00000143*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData04',           description='ASIC digital current',                                    offset=0x00000144*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData05',           description='Guard ring current',                                      offset=0x00000145*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData06',           description='Detector bias current',                                   offset=0x00000146*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData07',           description='Analog raw input voltage',                                offset=0x00000147*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='EnvData08',           description='Digital raw input voltage',                               offset=0x00000148*addrSize, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
  
      #####################################
      # Create commands
      #####################################
  
      self.add(pr.Command(name='masterReset',   description='Master Board Reset', function=pr.Command.postedTouch))
      self.add(pr.Command(name='fpgaReload',    description='Reload FPGA',        function=self.cmdFpgaReload))
      self.add(pr.Command(name='counterReset',  description='Counter Reset',      function='self.counter.post(0)'))
      self.add(pr.Command(name='testCpsw',      description='Test CPSW',          function=collections.OrderedDict({ 'masterResetVar': 1, 'usleep': 100, 'counter': 1 })))
  
      # Overwrite reset calls with local functions
      #self.setResetFunc(self.resetFunc)

   def cmdFpgaReload(dev,cmd,arg):
      """Example command function"""
      dev.Version.post(1)
   
   def resetFunc(dev,rstType):
      """Application specific reset function"""
      if rstType == 'soft':
         print('AxiVersion countReset')
      elif rstType == 'hard':
         dev.masterResetVar.post(1)
      elif rstType == 'count':
         print('AxiVersion countReset')

   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


################################################################################################
##
## Tixel Class definition
##
################################################################################################
class Tixel(pr.Device):
   def __init__(self, **kwargs):
      if 'description' not in kwargs:
            kwargs['description'] = "Tixel FPGA"
      
      trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'AsicPpbe', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
      inChaEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      inChbEnum={0:'Off', 16:'Asic0TpsMux', 17:'Asic1TpsMux'}
      
      super(self.__class__, self).__init__(**kwargs)
      self.add((
            axi.AxiVersion(offset=0x00000000),
            TixelFpgaRegisters(name="TixelFpgaRegisters", offset=0x01000000),
            TriggerRegisters(name="TriggerRegisters", offset=0x02000000, expand=False),
            SlowAdcRegisters(name="SlowAdcRegisters", offset=0x03000000, expand=False),
            epix.TixelAsic(name='TixelAsic0', offset=0x04000000, enabled=False, expand=False),
            epix.TixelAsic(name='TixelAsic1', offset=0x04400000, enabled=False, expand=False),
            AsicDeserRegisters(name='Asic0Deserializer', offset=0x0E000000, expand=False),
            AsicDeserRegisters(name='Asic1Deserializer', offset=0x0F000000, expand=False),
            AsicPktRegisters(name='Asic0PktRegisters', offset=0x10000000, expand=False),
            AsicPktRegisters(name='Asic1PktRegisters', offset=0x11000000, expand=False),
            pgp.Pgp2bAxi(name='Pgp2bAxi', offset=0x06000000, expand=False),
            analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[1].Adc[0]', offset=0x09000000, channels=4, enabled=False, expand=False),
            #analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[0]', offset=0x0A000000),    # not used in tixel, disabled by microblaze
            #analog_devices.Ad9249ConfigGroup(name='Ad9249Config[0].Adc[1]', offset=0x0A000800),    # not used in tixel, disabled by microblaze
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config[1].Adc[0]', offset=0x0A001000, enabled=False, expand=False),
            OscilloscopeRegisters(name='Oscilloscope', offset=0x0C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MicroblazeLog(name='MicroblazeLog', offset=0x0B000000, expand=False),
            MMCM7Registers(name='MMCM7Registers', offset=0x0D000000, enabled=False, expand=False)))
      

class TixelFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for Tixel"""
      super().__init__(description='Tixel Configuration Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      
      self.add(pr.Variable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='IdDigitalLow',    description='IdDigitalLow',      offset=0x00000004, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdDigitalHigh',   description='IdDigitalHigh',     offset=0x00000008, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdAnalogLow',     description='IdAnalogLow',       offset=0x0000000C, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdAnalogHigh',    description='IdAnalogHigh',      offset=0x00000010, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdCarrierLow',    description='IdCarrierLow',      offset=0x00000014, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='IdCarrierHigh',   description='IdCarrierHigh',     offset=0x00000018, bitSize=32, bitOffset=0, base='hex',  mode='RO'))
      self.add(pr.Variable(name='R0Polarity',      description='R0Polarity',        offset=0x00000100, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='R0Delay',         description='R0Delay',           offset=0x00000104, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='R0Width',         description='R0Width',           offset=0x00000108, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='GlblRstDelay',    description='GlblRstDelay',      offset=0x00000110, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='GlblRstWidth',    description='GlblRstWidth',      offset=0x00000114, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000118, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='AcqDelay1',       description='AcqDelay1',         offset=0x0000011C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqWidth1',       description='AcqWidth1',         offset=0x00000120, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqDelay2',       description='AcqDelay2',         offset=0x00000124, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='AcqWidth2',       description='AcqWidth2',         offset=0x00000128, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='TpulsePolarity',  description='TpulsePolarity',    offset=0x0000012C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='TpulseDelay',     description='TpulseDelay',       offset=0x00000130, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='TpulseWidth',     description='TpulseWidth',       offset=0x00000134, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='StartPolarity',   description='StartPolarity',     offset=0x00000138, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='StartDelay',      description='StartDelay',        offset=0x0000013C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='StartWidth',      description='StartWidth',        offset=0x00000140, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncPolarity',    description='SyncPolarity',      offset=0x0000015C, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SyncDelay',       description='SyncDelay',         offset=0x00000160, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SyncWidth',       description='SyncWidth',         offset=0x00000164, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000168, bitSize=1,  bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000016C, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      self.add(pr.Variable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000170, bitSize=32, bitOffset=0, base='uint', mode='RW'))
      
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
      self.add(pr.Variable(name='TixelDebugSel1',  description='TixelDebugSel1',    offset=0x00000218, bitSize=5,  bitOffset=0, base='hex',  mode='RW'))
      self.add(pr.Variable(name='TixelDebugSel2',  description='TixelDebugSel2',    offset=0x0000021C, bitSize=5,  bitOffset=0, base='hex',  mode='RW'))
      
      self.add(pr.Variable(name='AdcClkHalfT',     description='AdcClkHalfT',       offset=0x00000300, bitSize=32, bitOffset=0, base='uint', mode='RW'))
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
      self.add(pr.Variable(name='FrameSize',       description='FrameSize',      offset=0x00000004, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='FrameMaxSize',    description='FrameMaxSize',   offset=0x00000008, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='FrameMinSize',    description='FrameMinSize',   offset=0x0000000C, bitSize=16,  bitOffset=0, base='uint', mode='RO'))
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
      self.add(pr.Variable(name='ResetCounters',   description='ResetCounters',  offset=0x00000000, bitSize=1,   bitOffset=0, base='bool', mode='RW'))
      self.add(pr.Variable(name='frameRate',       description='frameRate',      offset=0x00000010, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='frameRateMax',    description='frameRateMax',   offset=0x00000014, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='frameRateMin',    description='frameRateMin',   offset=0x00000018, bitSize=32,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidth',       description='bandwidth',      offset=0x0000001C, bitSize=64,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidthMax',    description='bandwidthMax',   offset=0x00000024, bitSize=64,  bitOffset=0, base='uint', mode='RO'))
      self.add(pr.Variable(name='bandwidthMin',    description='bandwidthMin',   offset=0x0000002C, bitSize=64,  bitOffset=0, base='uint', mode='RO'))

      
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


