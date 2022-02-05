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
# PyRogue AXI Version Module for ePixHR family
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
import surf.protocols.ssp as ssp
import surf.devices.analog_devices as analog_devices
import surf.devices.micron as micron
import surf.misc
import surf
import epix_hr_core as epixHr
import numpy as np
import time

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *


#######################################################
#
# ePixHr 10kT Tx target
#
#######################################################

class EpixHR10kT(pr.Device):
    def __init__(self, **kwargs):
        if 'description' not in kwargs:
            kwargs['description'] = "HR Gen1 FPGA attached to ePixHr and ePix M test board"
      
        trigChEnum={0:'TrigReg', 1:'ThresholdChA', 2:'ThresholdChB', 3:'AcqStart', 4:'AsicAcq', 5:'AsicR0', 6:'AsicRoClk', 7:'AsicPpmat', 8:'PgpTrigger', 9:'AsicSync', 10:'AsicGr', 11:'AsicSaciSel0', 12:'AsicSaciSel1'}
        inChaEnum={0:'Asic0TpsMux', 1:'Asic1TpsMux', 2:'Asic2TpsMux', 3:'Asic3TpsMux'}
        inChbEnum={0:'Asic0TpsMux', 1:'Asic1TpsMux', 2:'Asic2TpsMux', 3:'Asic3TpsMux'}
        HsDacEnum={0:'None', 1:'DAC A (SE)', 2:'DAC B (Diff)', 3:'DAC A & DAC B'}
      
        super(self.__class__, self).__init__(**kwargs)
        self.add((
            # core registers
            #axi.AxiVersion(                                                    offset=0x00000000),
            #micron.AxiMicronN25Q(             name='MicronN25Q',               offset=0x02000000, expand=False, enabled=True),
            #pgp.Pgp4AxiL(                     name='Pgp4Axi_lane0',            offset=0x05000000, expand=False, enabled=False),
            #pgp.Pgp4AxiL(                     name='Pgp4Axi_lane1',            offset=0x05010000, expand=False, enabled=False),
            #pgp.Pgp4AxiL(                     name='Pgp4Axi_lane2',            offset=0x05020000, expand=False, enabled=False),
            #pgp.Pgp4AxiL(                     name='Pgp4Axi_lane3',            offset=0x05030000, expand=False, enabled=False),
            # app registers
            MMCM7Registers(                   name='MMCMRegisters',            offset=0x80000000, expand=False, enabled=False),
            TriggerRegisters(                 name="TriggerRegisters",         offset=0x81000000, expand=False, enabled=False),
            ssiPrbsTxRegisters(               name='ssiPrbs0PktRegisters',     offset=0x82000000, expand=False, enabled=False),
            ssiPrbsTxRegisters(               name='ssiPrbs1PktRegisters',     offset=0x83000000, expand=False, enabled=False),
            ssiPrbsTxRegisters(               name='ssiPrbs2PktRegisters',     offset=0x84000000, expand=False, enabled=False),
            ssiPrbsTxRegisters(               name='ssiPrbs3PktRegisters',     offset=0x85000000, expand=False, enabled=False),
            axi.AxiStreamMonAxiL(             name='AxiStreamMon',             offset=0x86000000, expand=False, enabled=False, numberLanes=4),
            axi.AxiMemTester(                 name='AxiMemTester',             offset=0x87000000, expand=False, enabled=False),
            epix.EpixHr10kTV2Asic(            name='Hr10kTAsic0',              offset=0x88000000, expand=False, enabled=False),
            epix.EpixHr10kTV2Asic(            name='Hr10kTAsic1',              offset=0x88400000, expand=False, enabled=False),
            epix.EpixHr10kTV2Asic(            name='Hr10kTAsic2',              offset=0x88800000, expand=False, enabled=False),
            epix.EpixHr10kTV2Asic(            name='Hr10kTAsic3',              offset=0x88C00000, expand=False, enabled=False),
            EPixHr10kTAppCoreFpgaRegisters(   name="RegisterControl",          offset=0x96000000, expand=False, enabled=False),
            powerSupplyRegisters(             name='PowerSupply',              offset=0x89000000, expand=False, enabled=False),            
            HighSpeedDacRegisters(            name='HSDac',                    offset=0x8A000000, expand=False, enabled=False,HsDacEnum=HsDacEnum),
            pr.MemoryDevice(                  name='waveformMem',              offset=0x8B000000, expand=False, wordBitSize=16, stride=4, size=1024*4),
            sDacRegisters(                    name='SlowDacs'    ,             offset=0x8C000000, expand=False, enabled=False),
            OscilloscopeRegisters(            name='Oscilloscope',             offset=0x8D000000, expand=False, enabled=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MonAdcRegisters(                  name='FastADCsDebug',            offset=0x8E000000, expand=False, enabled=False),
            analog_devices.Ad9249ConfigGroup( name='Ad9249Config_Adc_0',       offset=0x8F000000, expand=False, enabled=False),
            SlowAdcRegisters(                 name="SlowAdcRegisters",         offset=0x90000000, expand=False, enabled=False),
            ssp.SspLowSpeedDecoderReg(        name="SspLowSpeedDecoderReg",    offset=0x94010000, expand=False, enabled=False, numberLanes=24),
            DigitalAsicStreamAxi(             name="PacketRegisters0",         offset=0x95000000, expand=False, enabled=False, numberLanes=6), 
            DigitalAsicStreamAxi(             name="PacketRegisters1",         offset=0x95100000, expand=False, enabled=False, numberLanes=6), 
            DigitalAsicStreamAxi(             name="PacketRegisters2",         offset=0x95200000, expand=False, enabled=False, numberLanes=6), 
            DigitalAsicStreamAxi(             name="PacketRegisters3",         offset=0x95300000, expand=False, enabled=False, numberLanes=6)
        ))

        self.add(pr.LocalCommand(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.LocalCommand(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))
        self.add(pr.LocalCommand(name='InitASIC',   description='[routine, asic0, asic1, asic2, asic3]', value=[0,0,0,0,0] ,function=self.fnInitAsic))
        self.add(pr.LocalCommand(name='ASIC0_SDrst_SDclk_scan',      description='asic scan routine', function=self.fnScanSDrstSDClkScript))
        self.add(pr.LocalCommand(name='AcqDataWithSaciClkRst',      description='acquires a set of frame sending a clock reset between frames', function=self.fnAcqDataWithSaciClkRstScript))
        self.add(pr.LocalCommand(name='InitHSADC',   description='Initialize the HS ADC used by the scope module', value='' ,function=self.fnInitHsADC))


    def fnSetWaveform(self, dev,cmd,arg):
        """SetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            waveform = np.genfromtxt(self.filename, delimiter=',', dtype='uint16')
            if waveform.shape == (1024,):
                for x in range (0, 1024):
                    self.waveformMem._rawWrite(offset = (x * 4),data =  int(waveform[x]))
            else:
                print('wrong csv file format')

    def fnGetWaveform(self, dev,cmd,arg):
        """GetTestBitmap command function"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
        if os.path.splitext(self.filename)[1] == '.csv':
            readBack = np.zeros((1024),dtype='uint16')
            for x in range (0, 1024):
                readBack[x] = self.waveformMem._rawRead(offset = (x * 4))
            np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')


    def fnInitAsic(self, dev,cmd,arg):
        """SetTestBitmap command function"""       
        print("Rysync ASIC started")
        arguments = np.asarray(arg)
        if arguments[0] == 1:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_320MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_320MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 2:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_320MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_150us_320MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_320MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 3:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_320MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_320MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 4:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_320MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"                     
        if arguments[0] == 11:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_309MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 12:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_280MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 13:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_271MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 21:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_248MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 22:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_248MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_150us_248MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_248MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"
        if arguments[0] == 31:
            self.filenameMMCM              = "./yml/ePixHr10kT_MMCM_160MHz.yml"
            self.filenamePowerSupply       = "./yml/ePixHr10kT_PowerSupply_Enable.yml"
            self.filenameRegisterControl   = "./yml/ePixHr10kT_RegisterControl_24us_160MHz.yml"
            self.filenameASIC0             = "./yml/ePixHr10kT_PLLBypass_160MHz_ASIC_0.yml"
            self.filenameASIC1             = "./yml/ePixHr10kT_PLLBypass_160MHz_ASIC_1.yml"
            self.filenameASIC2             = "./yml/ePixHr10kT_PLLBypass_160MHz_ASIC_2.yml"
            self.filenameASIC3             = "./yml/ePixHr10kT_PLLBypass_160MHz_ASIC_3.yml"
            self.filenamePacketReg         = "./yml/ePixHr10kT_PacketRegisters.yml"
            self.filenameTriggerReg        = "./yml/ePixHr10kT_TriggerRegisters_100Hz.yml"

        
        if arguments[0] != 0:
            self.fnInitAsicScript(dev,cmd,arg)

    def fnInitAsicScript(self, dev,cmd,arg):
        """SetTestBitmap command function"""       
        print("Init ASIC script started")
        forcedDelay = 10
        delay = 1
        print("Loading MMCM configuration")
        self.MMCMRegisters.enable.set(True)
        self.root.readBlocks()
        time.sleep(delay/10) 
        self.root.LoadConfig(self.filenameMMCM)
        print(self.filenameMMCM)
        time.sleep(delay/10) 
        self.root.readBlocks()
        self.MMCMRegisters.enable.set(False)
        time.sleep(delay) 
        self.root.readBlocks()
        print("Completed")
		
        #Make sure triggers are not running
        self.TriggerRegisters.enable.set(True)
        self.TriggerRegisters.RunTriggerEnable.set(False)

        #Make sure clock is disabled at the ASIC level
        self.RegisterControl.enable.set(True)
        self.RegisterControl.ClkSyncEn.set(False)

        # load config that sets prog supply
        print("Loading supply configuration")
        self.PowerSupply.enable.set(True)
        self.PowerSupply.DigitalEn.set(False)
        self.PowerSupply.AnalogEn.set(False)
        time.sleep(delay) 
        self.root.LoadConfig(self.filenamePowerSupply)
        print(self.filenamePowerSupply)
        time.sleep(delay) 


        # load config that sets waveforms
        print("Loading register control (waveforms) configuration")
        self.root.LoadConfig(self.filenameRegisterControl)
        print(self.filenameRegisterControl)
        time.sleep(delay) 

        # load config that sets packet registers
        print("Loading packet registers")
        self.root.LoadConfig(self.filenamePacketReg)
        print(self.filenamePacketReg)
        time.sleep(delay)         

        ## takes the asic off of reset
        for i in range(1):
            print("Taking asic off of reset")            
            self.RegisterControl.GlblRstPolarity.set(False)
            time.sleep(delay) 
            self.RegisterControl.GlblRstPolarity.set(True)
            time.sleep(delay) 
            self.root.readBlocks()
            time.sleep(delay)

            ## load config for the asic
            print("Loading ASIC and timing configuration")
            #disable all asic to let the files define which ones should be set
            self.Hr10kTAsic0.enable.set(False)
            self.Hr10kTAsic1.enable.set(False)
            self.Hr10kTAsic2.enable.set(False)
            self.Hr10kTAsic3.enable.set(False)
            if arg[1] != 0:
                print("Loading ", self.filenameASIC0)
                self.root.LoadConfig(self.filenameASIC0)
                self.Hr10kTAsic0.ClearMatrix()
            if arg[2] != 0:
                print("Loading ", self.filenameASIC1)
                self.root.LoadConfig(self.filenameASIC1)
                self.Hr10kTAsic1.ClearMatrix()
            if arg[3] != 0:
                print("Loading ", self.filenameASIC2)
                self.root.LoadConfig(self.filenameASIC2)
                self.Hr10kTAsic2.ClearMatrix()
            if arg[4] != 0:
                print("Loading ", self.filenameASIC3)
                self.root.LoadConfig(self.filenameASIC3)
                self.Hr10kTAsic3.ClearMatrix()
			
            #Enable the ASIC clock for a bit while RSTreg is True and then turn it off again before removing RSTreg Commented to check?
           # self.RegisterControl.ClkSyncEn.set(True)
				
            if arg[1] != 0:
                print("Pulsing RSTreg ASIC0")        
                self.Hr10kTAsic0.RSTreg.set(True)
            if arg[2] != 0:
                print("Pulsing RSTreg ASIC1")
                self.Hr10kTAsic1.RSTreg.set(True)
            if arg[3] != 0:
                print("Pulsing RSTreg ASIC2")
                self.Hr10kTAsic2.RSTreg.set(True)
            if arg[4] != 0:
                print("Pulsing RSTreg ASIC3")
                self.Hr10kTAsic3.RSTreg.set(True)		
				
			#Disable the ASIC clock	
        #    self.RegisterControl.ClkSyncEn.set(False)
			#Pulse Sync Commented to check if works without sync
           # self.RegisterControl.SyncPolarity.set(True)
           # self.RegisterControl.SyncPolarity.set(False)
		
            if arg[1] != 0:      
                self.Hr10kTAsic0.RSTreg.set(False)
            if arg[2] != 0:
                self.Hr10kTAsic1.RSTreg.set(False)
            if arg[3] != 0:
                self.Hr10kTAsic2.RSTreg.set(False)
            if arg[4] != 0:
                self.Hr10kTAsic3.RSTreg.set(False)

        #time.sleep(forcedDelay) 
        # starting clock inside the ASIC
        self.RegisterControl.ClkSyncEn.set(True)
        
        ## load config for the asic
        print("Loading Trigger settings")
        self.root.LoadConfig(self.filenameTriggerReg)
        print(self.filenameTriggerReg)

        print("Initialization routine completed.")

    def fnAcqDataWithSaciClkRstScript(self, dev,cmd,arg):
        """SetTestBitmap command function"""       
        print("Acquiring data with clock reset between frames")            
        delay = 1
        numFrames = arg
        if numFrames == 0:
            numFrames = 100
        print("A total of %d frames will be added to the current file" % (numFrames))

        self.root.dataWriter.enable.set(True)
        self.currentFilename = self.root.dataWriter.dataFile.get()
        self.root.dataWriter.dataFile.set(self.currentFilename +"_refData"+".dat")

        print("Saving reference data")
        for frame in range(numFrames):
            #resync channels
            self.DeserRegisters0.Resync.set(True)
            self.DeserRegisters2.Resync.set(True)
            time.sleep(delay) 
            self.DeserRegisters0.Resync.set(False)
            self.DeserRegisters2.Resync.set(False)

            #enable to write frames          
            self.root.dataWriter.open.set(True)

            #acquire an image
            self.root.Trigger()
            time.sleep(delay) 
            
            #close file
            self.root.dataWriter.open.set(False)

            #no issued reset
            #self.Hr10kTAsic0.DigRO_disable.set(True)
            #self.Hr10kTAsic2.DigRO_disable.set(True)
            #self.Hr10kTAsic0.DigRO_disable.set(False)
            #self.Hr10kTAsic2.DigRO_disable.set(False)

        self.root.dataWriter.dataFile.set(self.currentFilename +"_testData"+".dat")
        print("Saving test data")
        for frame in range(numFrames):
            #resync channels
            self.DeserRegisters0.Resync.set(True)
            self.DeserRegisters2.Resync.set(True)
            time.sleep(delay) 
            self.DeserRegisters0.Resync.set(False)
            self.DeserRegisters2.Resync.set(False)

            #enable to write frames          
            self.root.dataWriter.open.set(True)

            #acquire an image
            self.root.Trigger()
            time.sleep(delay) 
            
            #close file
            self.root.dataWriter.open.set(False)

            #issue reset
            self.Hr10kTAsic0.DigRO_disable.set(True)
            self.Hr10kTAsic2.DigRO_disable.set(True)
            self.Hr10kTAsic0.DigRO_disable.set(False)
            self.Hr10kTAsic2.DigRO_disable.set(False)
        
            


    def fnScanSDrstSDClkScript(self, dev,cmd,arg):
        """SetTestBitmap command function"""       
        print("ASIC0 SDrst and SDclk scan started")
        print(arg)
        delay = 1
        self.root.readBlocks()
        #save filename
        self.root.dataWriter.enable.set(True)
        self.root.dataWriter.open.set(False)
        self.currentFilename = self.root.dataWriter.dataFile.get()

        # scan routine
        for SDrstValue  in range(16):
            for SDclkValue  in range(16):
                self.Hr10kTAsic0.SDrst_b.set(SDrstValue)
                self.Hr10kTAsic0.SDclk_b.set(SDclkValue)
                time.sleep(delay/5)               
                self.root.dataWriter.dataFile.set(self.currentFilename +"_SDrst_"+ str(SDrstValue)+"_SDclk_"+ str(SDclkValue)+".dat")
                self.root.dataWriter.open.set(True)
                # acquire data for 1 second
                time.sleep(delay)               
                self.root.dataWriter.open.set(False)       

        print("Completed")

    def fnInitHsADC(self, dev,cmd,arg):
        """Initialization routine for the HS ADC"""
        self.FastADCsDebug.enable.set(True)   
        self.FastADCsDebug.DelayAdc0.set(15)
        self.FastADCsDebug.enable.set(False)

        self.Ad9249Config_Adc_0.enable.set(True)
        self.root.readBlocks()
        self.FastADCsDebug.DelayAdc0.set(15)
        self.FastADCsDebug.enable.set(False)

        self.Ad9249Config_Adc_0.enable.set(True)
        self.root.readBlocks()
        self.Ad9249Config_Adc_0.InternalPdwnMode.set(3)
        self.Ad9249Config_Adc_0.InternalPdwnMode.set(0)
        self.Ad9249Config_Adc_0.OutputFormat.set(0)
        self.root.readBlocks()
        self.Ad9249Config_Adc_0.enable.set(False)
        self.root.readBlocks()
        print("Fast ADC initialized")

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
            axi.AxiStreamMonAxiL(    name='AxiStreamMon',                      offset=0x86000000, numberLanes=4,enabled=False, expand=False),
            axi.AxiMemTester(        name='AxiMemTester',                      offset=0x87000000, expand=False),
            powerSupplyRegisters(    name='PowerSupply',                       offset=0x88000000, expand=False),            
            HighSpeedDacRegisters(   name='HSDac',                             offset=0x89000000, expand=False,HsDacEnum=HsDacEnum),
            #pr.MemoryDevice(         name='waveformMem',                       offset=0x8A000000, wordBitSize=16, stride=4, size=1024*4),
            sDacRegisters(           name='SlowDacs'    ,                      offset=0x8B000000, enabled=False, expand=False),
            OscilloscopeRegisters(   name='Oscilloscope',                      offset=0x8C000000, expand=False, trigChEnum=trigChEnum, inChaEnum=inChaEnum, inChbEnum=inChbEnum),
            MonAdcRegisters(         name='FastADCsDebug',                     offset=0x8D000000, enabled=False, expand=False),
            #analog_devices.Ad9249ReadoutGroup(name = 'Ad9249Rdout[0].Adc[0]',  offset=0x8D000000, channels=4, enabled=False, expand=False),
            analog_devices.Ad9249ConfigGroup(name='Ad9249Config_Adc_0',    offset=0x8E000000, enabled=False, expand=False),
            SlowAdcRegisters(        name="SlowAdcRegisters",                  offset=0x8F000000, expand=False),
            ))

        self.add(pr.LocalCommand(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.LocalCommand(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))


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
            axi.AxiStreamMonAxiL(name='AxiStreamMon',               offset=0x87000000, enabled=False, expand=False),
            ))

        self.add(pr.LocalCommand(name='SetWaveform',description='Set test waveform for high speed DAC', function=self.fnSetWaveform))
        self.add(pr.LocalCommand(name='GetWaveform',description='Get test waveform for high speed DAC', function=self.fnGetWaveform))

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


##################################################################################
## ePix hr ePix M app register control 
##################################################################################
class EPixHrePixMAppCoreFpgaRegisters(pr.Device):
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
      
      self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x0000010C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000118, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay',          offset=0x0000011C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth',          offset=0x00000120, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay2',       description='AcqDelay',          offset=0x00000124, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth2',       description='AcqWidth',          offset=0x00000128, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='TPulsePolarity',  description='Polarity',          offset=0x0000012C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='TPulseDelay',     description='Delay',             offset=0x00000130, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='TPulseWidth',     description='Width',             offset=0x00000134, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='StartPolarity',   description='Polarity',          offset=0x00000138, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StartDelay',      description='Delay',             offset=0x0000013C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='StartWidth',      description='Width',             offset=0x00000140, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000144, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000148, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x0000014C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x00000150, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000154, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000158, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x0000015C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x00000160, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x00000164, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000168, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000016C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000170, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000174, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay1',       description='SR0Delay1',         offset=0x00000178, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width1',       description='SR0Width1',         offset=0x0000017C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='Vid',             description='Vid',               offset=0x00000180, bitSize=1,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrRstPolarity',  description='SSR Polarity',      offset=0x00000184, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ssrRstDelay',     description='SSR Delay1',        offset=0x00000188, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrWidth',        description='SSR Width1',        offset=0x0000018C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrSerialClrb',   description='SSR Serial clear',  offset=0x00000190, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ssrStorageClrb',  description='SSR Storage clear', offset=0x00000190, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ssrClkHalfT',     description='SSR period',        offset=0x00000194, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrClkDelay',     description='SSR delay',         offset=0x00000198, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrClkNumPeriods',description='SSR Num. rows',     offset=0x0000019C, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ssrData',         description='SSR Data 40 bits',  offset=0x000001A0, bitSize=40, bitOffset=0, base=pr.UInt, disp = '{:#x}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000200, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x00000208, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='AsicPwrEnable',         description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManual',         description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualDig',      description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualAna',      description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualIo',       description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualFpga',     description='AsicPower',         offset=0x0000020C, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000210, bitSize=32,bitOffset=0,  base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='DebugSel1',       description='TG connector sel.', offset=0x00000228, bitSize=5, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='DebugSel2',       description='MPS connector sel.',offset=0x0000022C, bitSize=5, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AdcClkHalfT',     description='',                  offset=0x00000300, bitSize=32,bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW'))
      self.add((
         pr.RemoteVariable(name='StartupReq',            description='AdcStartup',        offset=0x00000304, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',            description='AdcStartup',        offset=0x00000304, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail',           description='AdcStartup',        offset=0x00000304, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
     
     
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



##################################################################################
## ePix hr ePix M app register control 
##################################################################################
class EPixHr10kTAppCoreFpgaRegisters(pr.Device):
   def __init__(self, **kwargs):
      """Create the configuration device for HR Gen1 core FPGA registers"""
      """Version 1 is for ASIC 0.1 and test ADC ASIC"""
      """Version 2 is for ASIC 0.2 whee ClkSyncEn has been added"""

      version = 2
      
      super().__init__(description='HR Gen 1 core FPGA configuration registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      debugChEnum={0:'Asic01DM', 1:'AsicSync', 2:'AsicAcq', 3:'AsicSR0', 4:'AsicSaciClk', 5:'AsicSaciCmd', 6:'AsicSaciResp', 7:'AsicSaciSelL(0)', 8:'AsicSaciSelL(1)', 9:'AsicRdClk', 10:'deserClk', 11:'WFdacDin', 12:'WFdacSclk', 13:'WFdacCsL', 14:'WFdacLdacL', 15: 'WFdacCrtlL', 16: 'AsicGRst', 17: 'AsicR0', 18: 'SlowAdcDin', 19: 'SlowAdcDrdy', 20: 'SlowAdcDout', 21: 'slowAdcRefClk', 22: 'pgpTrigger', 23: 'acqStart'}

      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='Version',         description='Version',           offset=0x00000000, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{:#x}',  verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='GlblRstPolarity', description='GlblRstPolarity',   offset=0x00000100, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ClkSyncEn',       description='Enables clock to be available inside ASIC.',   offset=0x00000100, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncPolarity',    description='SyncPolarity',      offset=0x00000104, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SyncDelay',       description='SyncDelay',         offset=0x00000108, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SyncWidth',       description='SyncWidth',         offset=0x0000010C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Polarity',     description='SR0Polarity',       offset=0x00000110, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Delay1',       description='SR0Delay1',         offset=0x00000114, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SR0Width1',       description='SR0Width1',         offset=0x00000118, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ePixAdcSHPeriod', description='Period',            offset=0x0000011C, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='ePixAdcSHOffset', description='Offset',            offset=0x00000120, bitSize=16, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      
      self.add(pr.RemoteVariable(name='AcqPolarity',     description='AcqPolarity',       offset=0x00000200, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay1',       description='AcqDelay',          offset=0x00000204, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth1',       description='AcqWidth',          offset=0x00000208, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqDelay2',       description='AcqDelay',          offset=0x0000020C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='AcqWidth2',       description='AcqWidth',          offset=0x00000210, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='R0Polarity',      description='Polarity',          offset=0x00000214, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='R0Delay',         description='Delay',             offset=0x00000218, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='R0Width',         description='Width',             offset=0x0000021C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbePolarity',    description='PPbePolarity',      offset=0x00000220, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeDelay',       description='PPbeDelay',         offset=0x00000224, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PPbeWidth',       description='PPbeWidth',         offset=0x00000228, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatPolarity',   description='PpmatPolarity',     offset=0x0000022C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatDelay',      description='PpmatDelay',        offset=0x00000230, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='PpmatWidth',      description='PpmatWidth',        offset=0x00000234, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncPolarity',description='SaciSyncPolarity',  offset=0x00000238, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncDelay',   description='SaciSyncDelay',     offset=0x0000023C, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='SaciSyncWidth',   description='SaciSyncWidth',     offset=0x00000240, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))

      self.add(pr.RemoteVariable(name='AcqCnt',          description='AcqCnt',            offset=0x00000244, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SaciPrepRdoutCnt',description='SaciPrepRdoutCnt',  offset=0x00000248, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',     offset=0x0000024C, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
      self.add((
         pr.RemoteVariable(name='AsicPwrEnable',         description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=0,  base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManual',         description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=16, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualDig',      description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=20, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualAna',      description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=21, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualIo',       description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=22, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='AsicPwrManualFpga',     description='AsicPower',         offset=0x00000250, bitSize=1, bitOffset=23, base=pr.Bool, mode='RW')))
      self.add(pr.RemoteVariable(name='AsicMask',        description='AsicMask',          offset=0x00000254, bitSize=32,bitOffset=0,  base=pr.UInt, disp = '{:#x}',  mode='RO'))
      self.add(pr.RemoteVariable(name='DebugSel_TG',       description='TG connector sel.', offset=0x00000258, bitSize=5, bitOffset=0,  mode='RW', enum=debugChEnum))
      self.add(pr.RemoteVariable(name='DebugSel_MPS',       description='MPS connector sel.',offset=0x0000025C, bitSize=5, bitOffset=0,  mode='RW', enum=debugChEnum))
      self.add((
         pr.RemoteVariable(name='StartupReq',            description='AdcStartup',        offset=0x00000264, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='StartupAck',            description='AdcStartup',        offset=0x00000264, bitSize=1, bitOffset=1, base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='StartupFail',           description='AdcStartup',        offset=0x00000264, bitSize=1, bitOffset=2, base=pr.Bool, mode='RO')))
      
     
     
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
      self.add(pr.RemoteVariable(name='AcqCount',        description='AcqCount',          offset=0x00000024, bitSize=32, bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))

            
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
      self.add(pr.RemoteCommand(name='AcqCountReset', description='Resets Acq counter', 
                             offset=0x00000020, bitSize=1, bitOffset=0, function=pr.Command.touchOne))

   
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
      self.add(pr.RemoteVariable(name='lockedCountRst',     description='Frame ADC Idelay3 value',              offset=0x00000038, bitSize=1,  bitOffset=0,  base=pr.Bool, mode='RW'))

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
      self.add(pr.LocalCommand(name='InitAdcDelay',description='Find and set best delay for the adc channels', function=self.fnSetFindAndSetDelays))

   def fnSetFindAndSetDelays(self,dev,cmd,arg):
       """Find and set Monitoring ADC delays"""
       parent = self.parent
       if not(parent.Ad9249Config_Adc_0.enable.get()):
           parent.Ad9249Config_Adc_0.enable.set(True)
       
       parent.Ad9249Config_Adc_0.OutputTestMode.set(9) # one bit on
       self.testResult = np.zeros(256)
       #check adc 0
       for delay in range (0, 256):
           self.DelayAdc0.set(delay)
           self.testResult[delay] = (self.Adc0_0.get()==0x2AAA)
       print(self.testResult)
       #check adc 1
       
   
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
         pr.RemoteVariable(name='WFEnabled',       description='Enable waveform generation',                        offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='run',             description='Generates waveform when true',                      offset=0x00000000, bitSize=1,   bitOffset=1,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='externalUpdateEn',description='Updates value on AcqStart',                         offset=0x00000000, bitSize=1,   bitOffset=2,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='waveformSource',  description='Selects between custom wf or internal ramp',        offset=0x00000000, bitSize=2,   bitOffset=3,   base=pr.UInt, mode='RW'),
         pr.RemoteVariable(name='samplingCounter', description='Sampling period (>269, times 1/clock ref. 156MHz)', offset=0x00000004, bitSize=12,  bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='DacValue',        description='Set a fixed value for the DAC',                     offset=0x00000008, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW')
         ))
      
      self.add((pr.LinkVariable  (name='DacValueV' ,      linkedGet=self.convtFloat,        dependencies=[self.DacValue])));
      
      self.add((
         pr.RemoteVariable(name='DacChannel',      description='Select the DAC channel to use',                     offset=0x00000008, bitSize=2,   bitOffset=16,  mode='RW', enum=HsDacEnum),
         pr.RemoteVariable(name='rCStartValue',    description='Internal ramp generator start value',               offset=0x00000010, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='rCStopValue',     description='Internal ramp generator stop value',                offset=0x00000014, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW'),
         pr.RemoteVariable(name='rCStep',          description='Internal ramp generator step value',                offset=0x00000018, bitSize=16,  bitOffset=0,   base=pr.UInt, disp = '{}', mode='RW')
         ))
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
   @staticmethod
   def convtFloat(dev, var):
       value   = var.dependencies[0].get(read=False)
       fpValue = value*(2.5/65536.0)
       return '%0.3f'%(fpValue)               

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

##############################################################
##
## Clock Jitter Cleaner
## 
##############################################################
class ClockJitterCleanerRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Clock jitter cleaner Registers', **kwargs)
      
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
         pr.RemoteVariable(name='Lol',           description='Loss of Lock',                         offset=0x00000000, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='Los',           description='Loss of Signal',                       offset=0x00000000, bitSize=1,   bitOffset=1,   base=pr.Bool, mode='RO'),
         pr.RemoteVariable(name='RstL',          description='Reset active low',                     offset=0x00000004, bitSize=1,   bitOffset=0,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='Dec',           description='Skew decrement',                       offset=0x00000004, bitSize=1,   bitOffset=2,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='Inc',           description='Skew increment',                       offset=0x00000004, bitSize=1,   bitOffset=4,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='Frqtbl',        description='Frequency table select',               offset=0x00000004, bitSize=1,   bitOffset=6,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='FrqtblZ',       description='Tri-state driver',                     offset=0x00000004, bitSize=1,   bitOffset=7,   base=pr.Bool, mode='RW'),
         pr.RemoteVariable(name='Rate',          description='Rate selection',                       offset=0x00000008, bitSize=2,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='RateZ',         description='Tri-state driver',                     offset=0x00000008, bitSize=2,   bitOffset=2,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='BwSel',         description='Loop bandwidth select',                offset=0x0000000C, bitSize=2,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='BwSelZ',        description='Tri-state driver',                     offset=0x0000000C, bitSize=2,   bitOffset=2,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='FreqSel',       description='Frequency Select',                     offset=0x00000010, bitSize=4,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='FreqSelZ',      description='Tri-state driver',                     offset=0x00000010, bitSize=4,   bitOffset=4,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='Sfout',         description='Signal format select',                 offset=0x00000014, bitSize=2,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
         pr.RemoteVariable(name='SfoutZ',        description='Tri-state driver',                     offset=0x00000014, bitSize=2,   bitOffset=2,   base=pr.UInt, disp = '{:#x}', mode='RW')))
      
      
      
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
              pr.RemoteVariable(name='dac_0'  ,         description='',                  offset=0x00000, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),    
              pr.RemoteVariable(name='dac_1'  ,         description='',                  offset=0x00004, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
              pr.RemoteVariable(name='dac_2'  ,         description='',                  offset=0x00008, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
              pr.RemoteVariable(name='dac_3'  ,         description='',                  offset=0x0000C, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
              pr.RemoteVariable(name='dac_4'  ,         description='',                  offset=0x00010, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
              pr.RemoteVariable(name='dummy'  ,         description='',                  offset=0x00014, bitSize=32,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'))        
               )
      self.add((
              pr.LinkVariable  (name='Vdac_0' ,         linkedGet=self.convtFloat,        dependencies=[self.dac_0]),
              pr.LinkVariable  (name='Vdac_1' ,         linkedGet=self.convtFloat,        dependencies=[self.dac_1]),
              pr.LinkVariable  (name='Vdac_2' ,         linkedGet=self.convtFloat,        dependencies=[self.dac_2]),
              pr.LinkVariable  (name='Vdac_3' ,         linkedGet=self.convtFloat,        dependencies=[self.dac_3]),
              pr.LinkVariable  (name='Vdac_4' ,         linkedGet=self.convtFloat,        dependencies=[self.dac_4]))
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
   def convtFloat(dev, var):
        value   = var.dependencies[0].get(read=False)
        fpValue = value*(3.0/65536.0)
        return '%0.3f'%(fpValue)            
   
   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func

##############################################################
#programmable power supply
##############################################################
class ProgrammablePowerSupply(pr.Device):
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
                  pr.RemoteVariable(name='MVddAsic_dac_0',    description='',                  offset=0x00004, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),                
                  pr.RemoteVariable(name='MVh_dac_1',         description='',                  offset=0x00008, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),              
                  pr.RemoteVariable(name='MVbias_dac_2',      description='',                  offset=0x0000c, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
                  pr.RemoteVariable(name='MVm_dac_3',         description='',                  offset=0x00010, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),
                  pr.RemoteVariable(name='MVdd_det_dac_4',    description='',                  offset=0x00014, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'))
               )
      self.add((
                  pr.LinkVariable  (name='MVddAsic' ,         linkedGet=self.convtFloatP10p0,   dependencies=[self.MVddAsic_dac_0]),
                  pr.LinkVariable  (name='MVh' ,              linkedGet=self.convtFloatP7p0,    dependencies=[self.MVh_dac_1]),
                  pr.LinkVariable  (name='MVbias' ,           linkedGet=self.convtFloatP7p0,    dependencies=[self.MVbias_dac_2]),
                  pr.LinkVariable  (name='MVm' ,              linkedGet=self.convtFloatM2p5,    dependencies=[self.MVm_dac_3]),
                  pr.LinkVariable  (name='MVdd' ,             linkedGet=self.convtFloatP10p0,   dependencies=[self.MVdd_det_dac_4]))
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
   def convtFloatP10p0(dev, var):
        value   = var.dependencies[0].get(read=False)
        fpValue = value*(10.0/65536.0)
        return '%0.3f'%(fpValue)            

   @staticmethod
   def convtFloatM2p5(dev, var):
        value   = var.dependencies[0].get(read=False)
        fpValue = value*(-2.5/65536.0)
        return '%0.3f'%(fpValue)            

   @staticmethod
   def convtFloatP7p0(dev, var):
        value   = var.dependencies[0].get(read=False)
        fpValue = value*(7.0/65536.0)
        return '%0.3f'%(fpValue)            

   @staticmethod   
   def frequencyConverter(self):
      def func(dev, var):         
         return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
      return func


class ProgrammablePowerSupplyCryo(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Two channel programmable power supply', **kwargs)
      
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
                  pr.RemoteVariable(name='Vdd1',    description='',                  offset=0x00004, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'),                
                  pr.RemoteVariable(name='Vdd2',    description='',                  offset=0x00008, bitSize=16,   bitOffset=0,   base=pr.UInt, disp = '{:#x}', mode='RW'))
               )
      self.add((
                  pr.LinkVariable  (name='Vdd1_V',         linkedGet=self.convtFloatP5p0,    dependencies=[self.Vdd1]),
                  pr.LinkVariable  (name='Vdd2_V',         linkedGet=self.convtFloatP5p0,    dependencies=[self.Vdd2]))
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
   def convtFloatP5p0(dev, var):
        value   = var.dependencies[0].get(read=False)
        fpValue = value*(5.0/65536.0)
        return '%0.3f'%(fpValue)            

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
      self.add(pr.RemoteVariable(name='rstStateMachine', description='Reset Read SM',     offset=0x00000008, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))
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

      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',                                  offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',                                   offset=0x00000004, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',                                offset=0x00000008, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',                                offset=0x0000000C, bitSize=32,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='SofErrors',       description='SofErrors',                                   offset=0x00000010, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='EofErrors',       description='EofErrors',                                   offset=0x00000014, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='OverflowErrors',  description='OverflowErrors',                              offset=0x00000018, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='TestModeCh0',     description='TestMode',                                    offset=0x0000001C, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='TestModeCh1',     description='TestMode',                                    offset=0x0000001C, bitSize=1,   bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='forceAdcData',    description='TestMode',                                    offset=0x0000001C, bitSize=1,   bitOffset=2, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='decDataBitOrder', description='when enabled reverse bit order',              offset=0x0000001C, bitSize=1,   bitOffset=3, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='decBypass',       description='bypass decoder to display 14 bit data.',      offset=0x0000001C, bitSize=1,   bitOffset=4, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StreamDataMode',  description='Streams data cont.',                          offset=0x00000020, bitSize=1,   bitOffset=0, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='StopDataTx',      description='Interrupt data stream',                       offset=0x00000020, bitSize=1,   bitOffset=1, base=pr.Bool, mode='RW'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',                               offset=0x00000024, bitSize=1,   bitOffset=0, base=pr.Bool, mode='WO'))
      self.add(pr.RemoteVariable(name='asicDataReq',     description='Number of samples requested per ADC stream.', offset=0x00000028, bitSize=16,  bitOffset=0, base=pr.UInt, disp = '{}', mode='RW'))
      self.add(pr.RemoteVariable(name='DisableLane',     description='Disable selected lanes.',                     offset=0x0000002C, bitSize=24,  bitOffset=0, base=pr.UInt, mode='RW'))
      
class DigitalAsicStreamAxi(pr.Device):
   def __init__(self, numberLanes=1, **kwargs):
      super().__init__(description='Asic data packet registers', **kwargs)
      
      #Setup registers & variables
      
      self.add(pr.RemoteVariable(name='FrameCount',      description='FrameCount',                                  offset=0x00000000, bitSize=32,  bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='FrameSize',       description='FrameSize',                                   offset=0x00000004, bitSize=16,  bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMaxSize',    description='FrameMaxSize',                                offset=0x00000008, bitSize=16,  bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='FrameMinSize',    description='FrameMinSize',                                offset=0x0000000C, bitSize=16,  bitOffset=0, base=pr.UInt, mode='RO'))
      self.add(pr.RemoteVariable(name='ResetCounters',   description='ResetCounters',                               offset=0x00000024, bitSize=1,   bitOffset=0, base=pr.Bool, mode='WO'))
      self.add(pr.RemoteVariable(name='asicDataReq',     description='Number of samples requested per ADC stream.', offset=0x00000028, bitSize=16,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='DisableLane',     description='Disable selected lanes.',                     offset=0x0000002C, bitSize=numberLanes,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='EnumerateDisLane',description='Insert lane number into disabled lane.',      offset=0x00000030, bitSize=numberLanes,  bitOffset=0, base=pr.UInt, mode='RW'))
      self.add(pr.RemoteVariable(name='gainBitRemapped', description='Set true to move gain bit (bit(0)) to MSB.',  offset=0x00000034, bitSize=numberLanes,  bitOffset=0, base=pr.UInt, mode='RW'))
      
      self.addRemoteVariables(
         name         = 'TimeoutCntLane',
         offset       = 0x100,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataCntLaneAct',
         offset       = 0x200,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataCntLaneReg',
         offset       = 0x300,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataCntLaneMin',
         offset       = 0x400,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataCntLaneMax',
         offset       = 0x500,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataDlyLaneReg',
         offset       = 0x600,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
      self.addRemoteVariables(
         name         = 'DataOvfLane',
         offset       = 0x700,
         bitSize      = 16,
         mode         = 'RO',
         number       = numberLanes,
         stride       = 4,
         pollInterval = 1,
      )
      
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


############################################################################
## Deserializers HR 16bit
############################################################################
class AsicDeserHr16bRegisters(pr.Device):
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
      self.add(pr.RemoteVariable(name='StreamsEn_n',  description='Enable/Disable', offset=0x00000000, bitSize=2,  bitOffset=0,  base=pr.UInt, mode='RW'))    
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',         offset=0x00000004, bitSize=1,  bitOffset=0,  base=pr.Bool, verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='Delay0_', description='Data ADC Idelay3 value', offset=0x00000010, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay0',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay0_]))
      self.add(pr.RemoteVariable(name='Delay1_', description='Data ADC Idelay3 value', offset=0x00000014, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay1',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay1_]))
      self.add(pr.RemoteVariable(name='LockErrors0',  description='LockErrors',     offset=0x00000030, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked0',      description='Locked',         offset=0x00000030, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors1',  description='LockErrors',     offset=0x00000034, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked1',      description='Locked',         offset=0x00000034, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))

      for i in range(0, 2):
         self.add(pr.RemoteVariable(name='IserdeseOutA'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000080+i*4, bitSize=20, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))

      for i in range(0, 2):
         self.add(pr.RemoteVariable(name='IserdeseOutB'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000088+i*4, bitSize=20, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))
      self.add(AsicDeser10bDataRegisters(name='tenbData_ser0',      offset=0x00000100, expand=False))
      self.add(AsicDeser10bDataRegisters(name='tenbData_ser1',      offset=0x00000200, expand=False))
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed

      self.add(pr.LocalCommand(name='InitAdcDelay',description='Find and set best delay for the adc channels', function=self.fnSetFindAndSetDelays))
      

   def fnSetFindAndSetDelays(self,dev,cmd,arg):
       """Find and set Monitoring ADC delays"""
       parent = self.parent
       numDelayTaps = 512
       self.IDLE_PATTERN1 = 0xAAA83
       self.IDLE_PATTERN2 = 0xAA97C
       print("Executing delay test for ePixHr")

       self.testResult0 = np.zeros(numDelayTaps)
       self.testDelay0  = np.zeros(numDelayTaps)
       #check adc 0
       for delay in range (0, numDelayTaps):
           self.Delay0.set(delay)
           self.testDelay0[delay] = self.Delay0.get()
           self.Resync.set(True)
           self.Resync.set(False)
           time.sleep(1.0 / float(100))
           self.testResult0[delay] = ((self.IserdeseOutA0.get()==self.IDLE_PATTERN1)or(self.IserdeseOutA0.get()==self.IDLE_PATTERN2)) 
       print("Test result adc 0:")
       print(self.testResult0*self.testDelay0)

       #check adc 1   
       self.testResult1 = np.zeros(numDelayTaps)
       self.testDelay1  = np.zeros(numDelayTaps)
       for delay in range (0, numDelayTaps):
           self.Delay1.set(delay)
           self.testDelay1[delay] = self.Delay1.get()
           self.Resync.set(True)
           self.Resync.set(False)
           time.sleep(1.0 / float(100))
           self.testResult1[delay] = ((self.IserdeseOutA1.get()==self.IDLE_PATTERN1)or(self.IserdeseOutA1.get()==self.IDLE_PATTERN2)) 
       print("Test result adc 1:")     
       print(self.testResult1*self.testDelay1)
       
       self.resultArray0 =  np.zeros(numDelayTaps)
       self.resultArray1 =  np.zeros(numDelayTaps)
       for i in range(1, numDelayTaps):
           if (self.testResult0[i] != 0):
               self.resultArray0[i] = self.resultArray0[i-1] + self.testResult0[i]
           if (self.testResult1[i] != 0):
               self.resultArray1[i] = self.resultArray1[i-1] + self.testResult1[i]
       self.longestDelay0 = np.where(self.resultArray0==np.max(self.resultArray0))
       if len(self.longestDelay0[0])==1:
           self.sugDelay0 = int(self.longestDelay0[0]) - int(self.resultArray0[self.longestDelay0]/2)
       else:
           self.sugDelay0 = int(self.longestDelay0[0][0]) - int(self.resultArray0[self.longestDelay0[0][0]]/2)
       self.longestDelay1 = np.where(self.resultArray1==np.max(self.resultArray1))
       if len(self.longestDelay1[0])==1:
           self.sugDelay1 = int(self.longestDelay1[0]) - int(self.resultArray1[self.longestDelay1]/2)
       else:
           self.sugDelay1 = int(self.longestDelay1[0][0]) - int(self.resultArray1[self.longestDelay1[0][0]]/2)
       print("Suggested delay_0: " + str(self.sugDelay0))     
       print("Suggested delay_1: " + str(self.sugDelay1))     

   
   @staticmethod   
   def setDelay(var, value, write):
      iValue = value + 512
      var.dependencies[0].set(iValue, write)
      var.dependencies[0].set(value, write)

   @staticmethod   
   def getDelay(var, read):
      return var.dependencies[0].get(read)




class AsicDeserHr16bRegisters6St(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='20 bit Deserializer Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      self.add(pr.RemoteVariable(name='StreamsEn_n',  description='Enable/Disable', offset=0x00000000, bitSize=6,  bitOffset=0,  base=pr.UInt, mode='RW'))    
      self.add(pr.RemoteVariable(name=('IdelayRst'),     description='iDelay reset',  offset=0x00000008, bitSize=6, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RW'))
      self.add(pr.RemoteVariable(name=('IserdeseRst'),   description='iSerdese3 reset',  offset=0x0000000C, bitSize=6, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RW'))
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',         offset=0x00000004, bitSize=1,  bitOffset=0,  base=pr.Bool, verify = False, mode='RW'))
      self.add(pr.RemoteVariable(name='Delay0_', description='Data ADC Idelay3 value', offset=0x00000010, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay0',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay0_]))
      self.add(pr.RemoteVariable(name='Delay1_', description='Data ADC Idelay3 value', offset=0x00000014, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay1',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay1_]))
      self.add(pr.RemoteVariable(name='Delay2_', description='Data ADC Idelay3 value', offset=0x00000018, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay2',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay2_]))
      self.add(pr.RemoteVariable(name='Delay3_', description='Data ADC Idelay3 value', offset=0x0000001C, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay3',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay3_]))
      self.add(pr.RemoteVariable(name='Delay4_', description='Data ADC Idelay3 value', offset=0x00000020, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay4',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay4_]))
      self.add(pr.RemoteVariable(name='Delay5_', description='Data ADC Idelay3 value', offset=0x00000024, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay5',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay5_]))
      self.add(pr.RemoteVariable(name='LockErrors0',  description='LockErrors',     offset=0x00000030, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked0',      description='Locked',         offset=0x00000030, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors1',  description='LockErrors',     offset=0x00000034, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked1',      description='Locked',         offset=0x00000034, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors2',  description='LockErrors',     offset=0x00000038, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked2',      description='Locked',         offset=0x00000038, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors3',  description='LockErrors',     offset=0x0000003C, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked3',      description='Locked',         offset=0x0000003C, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors4',  description='LockErrors',     offset=0x00000040, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked4',      description='Locked',         offset=0x00000040, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))
      self.add(pr.RemoteVariable(name='LockErrors5',  description='LockErrors',     offset=0x00000044, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked5',      description='Locked',         offset=0x00000044, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))

      for j in range(0, 6):
          for i in range(0, 2):
              self.add(pr.RemoteVariable(name=('IserdeseOut%d_%d' % (j, i)),   description='IserdeseOut'+str(i),  offset=0x00000080+i*4+j*8, bitSize=20, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))

      self.add(pr.RemoteVariable(name='FreezeDebug',      description='Restart BERT',  offset=0x00000100, bitSize=1,  bitOffset=0, base=pr.Bool, mode='RW'))      
      self.add(pr.RemoteVariable(name='BERTRst',      description='Restart BERT',      offset=0x00000100, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))      
      for i in range(0, 6):
         self.add(pr.RemoteVariable(name='BERTCounter'+str(i),   description='Counter value.'+str(i),  offset=0x00000104+i*8, bitSize=44, bitOffset=0, base=pr.UInt,  disp = '{}', mode='RO'))

      for i in range(0,6):
          self.add(AsicDeser10bDataRegisters(name='tenbData_ser%d'%i,      offset=(0x00000200+(i*0x00000100)), expand=False))
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed

      self.add(pr.LocalCommand(name='InitAdcDelay',description='Find and set best delay for the adc channels', function=self.fnSetFindAndSetDelays))
      self.add(pr.LocalCommand(name='Refines delay settings',description='Find and set best delay for the adc channels', function=self.fnRefineDelays))
      

   def fnSetFindAndSetDelays(self,dev,cmd,arg):
       """Find and set Monitoring ADC delays"""
       parent = self.parent
       numDelayTaps = 512
       self.IDLE_PATTERN1 = 0xAAA83
       self.IDLE_PATTERN2 = 0xAA97C
       print("Executing delay test for ePixHr")

       #check adcs
       self.testResult = np.zeros((6,numDelayTaps))
       self.testDelay  = np.zeros((6,numDelayTaps))
       for delay in range (0, numDelayTaps):
           self.Delay0.set(delay)
           self.Delay1.set(delay)
           self.Delay2.set(delay)
           self.Delay3.set(delay)
           self.Delay4.set(delay)
           self.Delay5.set(delay)
           self.testDelay[0,delay] = self.Delay0.get()
           self.testDelay[1,delay] = self.Delay1.get()
           self.testDelay[2,delay] = self.Delay2.get()
           self.testDelay[3,delay] = self.Delay3.get()
           self.testDelay[4,delay] = self.Delay4.get()
           self.testDelay[5,delay] = self.Delay5.get()
           self.Resync.set(True)
           self.Resync.set(False)
           time.sleep(1.0 / float(100))
           IserdeseOut_value = self.IserdeseOut0_0.get()
           self.testResult[0,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))
           IserdeseOut_value = self.IserdeseOut1_0.get()
           self.testResult[1,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2)) 
           IserdeseOut_value = self.IserdeseOut2_0.get()
           self.testResult[2,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2)) 
           IserdeseOut_value = self.IserdeseOut3_0.get()
           self.testResult[3,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2)) 
           IserdeseOut_value = self.IserdeseOut4_0.get()
           self.testResult[4,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2)) 
           IserdeseOut_value = self.IserdeseOut5_0.get()
           self.testResult[5,delay] = ((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2)) 
       print("Test result adc 0:")     
       print(self.testResult[0,:]*self.testDelay)
       print("Test result adc 1:")     
       print(self.testResult[1,:]*self.testDelay)
       print("Test result adc 2:")     
       print(self.testResult[2,:]*self.testDelay)
       print("Test result adc 3:")     
       print(self.testResult[3,:]*self.testDelay)
       print("Test result adc 4:")     
       print(self.testResult[4,:]*self.testDelay)
       print("Test result adc 5:")     
       print(self.testResult[5,:]*self.testDelay)
       np.savetxt(str(self.name)+'_delayTestResultAll.csv', (self.testResult*self.testDelay), delimiter=',') 


       
       
       self.resultArray =  np.zeros((6,numDelayTaps))
       for j in range(0, 6):
           for i in range(1, numDelayTaps):
               if (self.testResult[j,i] != 0):
                   self.resultArray[j,i] = self.resultArray[j,i-1] + self.testResult[j,i]

       self.longestDelay0 = np.where(self.resultArray[0]==np.max(self.resultArray[0]))
       if len(self.longestDelay0[0])==1:
           self.sugDelay0 = int(self.longestDelay0[0]) - int(self.resultArray[0][self.longestDelay0]/2)
       else:
           self.sugDelay0 = int(self.longestDelay0[0][0]) - int(self.resultArray[0][self.longestDelay0[0][0]]/2)

       self.longestDelay1 = np.where(self.resultArray[1]==np.max(self.resultArray[1]))
       if len(self.longestDelay1[0])==1:
           self.sugDelay1 = int(self.longestDelay1[0]) - int(self.resultArray[1][self.longestDelay1]/2)
       else:
           self.sugDelay1 = int(self.longestDelay1[0][0]) - int(self.resultArray[1][self.longestDelay1[0][0]]/2)

       self.longestDelay2 = np.where(self.resultArray[2]==np.max(self.resultArray[2]))
       if len(self.longestDelay2[0])==1:
           self.sugDelay2 = int(self.longestDelay2[0]) - int(self.resultArray[2][self.longestDelay2]/2)
       else:
           self.sugDelay2 = int(self.longestDelay2[0][0]) - int(self.resultArray[2][self.longestDelay2[0][0]]/2)

       self.longestDelay3 = np.where(self.resultArray[3]==np.max(self.resultArray[3]))
       if len(self.longestDelay3[0])==1:
           self.sugDelay3 = int(self.longestDelay3[0]) - int(self.resultArray[3][self.longestDelay3]/2)
       else:
           self.sugDelay3 = int(self.longestDelay3[0][0]) - int(self.resultArray[3][self.longestDelay3[0][0]]/2)

       self.longestDelay4 = np.where(self.resultArray[4]==np.max(self.resultArray[4]))
       if len(self.longestDelay4[0])==1:
           self.sugDelay4 = int(self.longestDelay4[0]) - int(self.resultArray[4][self.longestDelay4]/2)
       else:
           self.sugDelay4 = int(self.longestDelay4[0][0]) - int(self.resultArray[4][self.longestDelay4[0][0]]/2)

       self.longestDelay5 = np.where(self.resultArray[5]==np.max(self.resultArray[5]))
       if len(self.longestDelay5[0])==1:
           self.sugDelay5 = int(self.longestDelay5[0]) - int(self.resultArray[5][self.longestDelay5]/2)
       else:
           self.sugDelay5 = int(self.longestDelay5[0][0]) - int(self.resultArray[5][self.longestDelay5[0][0]]/2)
       #self.longestDelay1 = np.where(self.resultArray1==np.max(self.resultArray1))
       #if len(self.longestDelay1[0])==1:
       #    self.sugDelay1 = int(self.longestDelay1[0]) - int(self.resultArray1[self.longestDelay1]/2)
       #else:
       #    self.sugDelay1 = int(self.longestDelay1[0][0]) - int(self.resultArray1[self.longestDelay1[0][0]]/2)
       print("Suggested delay_0: " + str(self.sugDelay0))     
       print("Suggested delay_1: " + str(self.sugDelay1))
       print("Suggested delay_2: " + str(self.sugDelay2))     
       print("Suggested delay_3: " + str(self.sugDelay3))     
       print("Suggested delay_4: " + str(self.sugDelay4))     
       print("Suggested delay_5: " + str(self.sugDelay5))     
       # apply suggested settings
       self.Delay0.set(self.sugDelay0)
       self.Delay1.set(self.sugDelay1)
       self.Delay2.set(self.sugDelay2)
       self.Delay3.set(self.sugDelay3)
       self.Delay4.set(self.sugDelay4)
       self.Delay5.set(self.sugDelay5)
       self.Resync.set(True)
       time.sleep(1.0 / float(100))
       self.Resync.set(False)


   def fnRefineDelays(self,dev,cmd,arg):
       """Find and set Monitoring ADC delays"""
       parent = self.parent
       numDelayTaps = 512
       self.IDLE_PATTERN1 = 0xAAA83
       self.IDLE_PATTERN2 = 0xAA97C
       print("Executing delay test for ePixHr")

       #check adcs
       self.testResult = np.zeros((6,numDelayTaps))
       self.testDelay  = np.zeros((6,numDelayTaps))
       for delay in range (0, numDelayTaps):
           self.Delay0.set(delay)
           self.Delay1.set(delay)
           self.Delay2.set(delay)
           self.Delay3.set(delay)
           self.Delay4.set(delay)
           self.Delay5.set(delay)
           time.sleep(1.0 / float(100))
           self.testDelay[0,delay] = self.Delay0.get()
           self.testDelay[1,delay] = self.Delay1.get()
           self.testDelay[2,delay] = self.Delay2.get()
           self.testDelay[3,delay] = self.Delay3.get()
           self.testDelay[4,delay] = self.Delay4.get()
           self.testDelay[5,delay] = self.Delay5.get()
           ###
           #self.Resync.set(True)
           #self.Resync.set(False)
           ###
           time.sleep(1.0 / float(100))
           for checks in range(0,10):
               IserdeseOut_value = self.IserdeseOut0_0.get()
               self.testResult[0,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[0,delay]))
               IserdeseOut_value = self.IserdeseOut1_0.get()
               self.testResult[1,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[1,delay])) 
               IserdeseOut_value = self.IserdeseOut2_0.get()
               self.testResult[2,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[2,delay])) 
               IserdeseOut_value = self.IserdeseOut3_0.get()
               self.testResult[3,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[3,delay])) 
               IserdeseOut_value = self.IserdeseOut4_0.get()
               self.testResult[4,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[4,delay])) 
               IserdeseOut_value = self.IserdeseOut5_0.get()
               self.testResult[5,delay] = (((IserdeseOut_value==self.IDLE_PATTERN1)or(IserdeseOut_value==self.IDLE_PATTERN2))+(self.testResult[5,delay])) 
       print("Test result adc 0:")     
       print(self.testResult[0,:]*self.testDelay)
       print("Test result adc 1:")     
       print(self.testResult[1,:]*self.testDelay)
       print("Test result adc 2:")     
       print(self.testResult[2,:]*self.testDelay)
       print("Test result adc 3:")     
       print(self.testResult[3,:]*self.testDelay)
       print("Test result adc 4:")     
       print(self.testResult[4,:]*self.testDelay)
       print("Test result adc 5:")     
       print(self.testResult[5,:]*self.testDelay)
       #np.savetxt(str(self.name)+'_delayRefineTestResultAll.csv', (self.testResult*self.testDelay), delimiter=',') 
       np.savetxt(str(self.name)+'_delayRefineTestResultAll.csv', (self.testResult), delimiter=',') 
       
       self.resultArray =  np.zeros((6,numDelayTaps))
       for j in range(0, 6):
           for i in range(1, numDelayTaps):
               if (self.testResult[j,i] != 0):
                   self.resultArray[j,i] = self.resultArray[j,i-1] + 1 #self.testResult[j,i]

       self.longestDelay0 = np.where(self.resultArray[0]==np.max(self.resultArray[0]))
       if len(self.longestDelay0[0])==1:
           self.sugDelay0 = int(self.longestDelay0[0]) - int(self.resultArray[0][self.longestDelay0]/2)
       else:
           self.sugDelay0 = int(self.longestDelay0[0][0]) - int(self.resultArray[0][self.longestDelay0[0][0]]/2)

       self.longestDelay1 = np.where(self.resultArray[1]==np.max(self.resultArray[1]))
       if len(self.longestDelay1[0])==1:
           self.sugDelay1 = int(self.longestDelay1[0]) - int(self.resultArray[1][self.longestDelay1]/2)
       else:
           self.sugDelay1 = int(self.longestDelay1[0][0]) - int(self.resultArray[1][self.longestDelay1[0][0]]/2)

       self.longestDelay2 = np.where(self.resultArray[2]==np.max(self.resultArray[2]))
       if len(self.longestDelay2[0])==1:
           self.sugDelay2 = int(self.longestDelay2[0]) - int(self.resultArray[2][self.longestDelay2]/2)
       else:
           self.sugDelay2 = int(self.longestDelay2[0][0]) - int(self.resultArray[2][self.longestDelay2[0][0]]/2)

       self.longestDelay3 = np.where(self.resultArray[3]==np.max(self.resultArray[3]))
       if len(self.longestDelay3[0])==1:
           self.sugDelay3 = int(self.longestDelay3[0]) - int(self.resultArray[3][self.longestDelay3]/2)
       else:
           self.sugDelay3 = int(self.longestDelay3[0][0]) - int(self.resultArray[3][self.longestDelay3[0][0]]/2)

       self.longestDelay4 = np.where(self.resultArray[4]==np.max(self.resultArray[4]))
       if len(self.longestDelay4[0])==1:
           self.sugDelay4 = int(self.longestDelay4[0]) - int(self.resultArray[4][self.longestDelay4]/2)
       else:
           self.sugDelay4 = int(self.longestDelay4[0][0]) - int(self.resultArray[4][self.longestDelay4[0][0]]/2)

       self.longestDelay5 = np.where(self.resultArray[5]==np.max(self.resultArray[5]))
       if len(self.longestDelay5[0])==1:
           self.sugDelay5 = int(self.longestDelay5[0]) - int(self.resultArray[5][self.longestDelay5]/2)
       else:
           self.sugDelay5 = int(self.longestDelay5[0][0]) - int(self.resultArray[5][self.longestDelay5[0][0]]/2)
       print("Suggested delay_0: " + str(self.sugDelay0))     
       print("Suggested delay_1: " + str(self.sugDelay1))
       print("Suggested delay_2: " + str(self.sugDelay2))     
       print("Suggested delay_3: " + str(self.sugDelay3))     
       print("Suggested delay_4: " + str(self.sugDelay4))     
       print("Suggested delay_5: " + str(self.sugDelay5))     
       # apply suggested settings
       self.Delay0.set(self.sugDelay0)
       self.Delay1.set(self.sugDelay1)
       self.Delay2.set(self.sugDelay2)
       self.Delay3.set(self.sugDelay3)
       self.Delay4.set(self.sugDelay4)
       self.Delay5.set(self.sugDelay5)
       ###
       #self.Resync.set(True)
       #time.sleep(1.0 / float(100))
       #self.Resync.set(False)
       ###

   
   @staticmethod   
   def setDelay(var, value, write):
      iValue = value + 512
      var.dependencies[0].set(iValue, write)
      var.dependencies[0].set(value, write)

   @staticmethod   
   def getDelay(var, read):
      return var.dependencies[0].get(read)

   

############################################################################
## Deserializers HR 12bit
############################################################################
class AsicDeserHr12bRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='Ultrascale Series 14 bit Deserializer Registers', **kwargs)
      
      # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
      # contains this object. In most cases the parent and memBase are the same but they can be 
      # different in more complex bus structures. They will also be different for the top most node.
      # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
      # blocks will be updated.
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables
      self.add(pr.RemoteVariable(name='StreamsEn_n',  description='Enable/Disable', offset=0x00000000, bitSize=2,  bitOffset=0,  base=pr.UInt, mode='RW'))    
      self.add(pr.RemoteVariable(name='Resync',       description='Resync',         offset=0x00000004, bitSize=1,  bitOffset=0,  base=pr.Bool, verify = False, mode='RW'))


      self.add(pr.RemoteVariable(name='Delay0_', description='Data ADC Idelay3 value', offset=0x00000010, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay0',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay0_]))
      #self.add(pr.RemoteVariable(name='Delay0',       description='Delay',          offset=0x00000010, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      #self.add(pr.RemoteVariable(name='SerDesDelay0', description='DelayValue',     offset=0x00000010, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW', verify = False))
      #self.add(pr.RemoteVariable(name='DelayEn0',     description='EnValueUpdate',  offset=0x00000010, bitSize=1,  bitOffset=9,  base=pr.Bool, verify = False, mode='RW'))

      self.add(pr.RemoteVariable(name='LockErrors0',  description='LockErrors',     offset=0x00000030, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked0',      description='Locked',         offset=0x00000030, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))      
      
      self.add(pr.RemoteVariable(name='Delay1_', description='Data ADC Idelay3 value', offset=0x00000014, bitSize=10,  bitOffset=0,  base=pr.UInt, disp = '{}', verify=False, mode='RW', hidden=True))
      self.add(pr.LinkVariable(  name='Delay1',  description='Data ADC Idelay3 value', linkedGet=self.getDelay, linkedSet=self.setDelay, dependencies=[self.Delay1_]))
      #self.add(pr.RemoteVariable(name='Delay1',       description='Delay',          offset=0x00000014, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      #self.add(pr.RemoteVariable(name='SerDesDelay1', description='DelayValue',     offset=0x00000014, bitSize=9,  bitOffset=0,  base=pr.UInt, disp = '{}', mode='RW', verify = False))
      #self.add(pr.RemoteVariable(name='DelayEn1',     description='EnValueUpdate',  offset=0x00000014, bitSize=1,  bitOffset=9,  base=pr.Bool, verify = False, mode='RW'))

      self.add(pr.RemoteVariable(name='LockErrors1',  description='LockErrors',     offset=0x00000034, bitSize=16, bitOffset=0,  base=pr.UInt, disp = '{}', mode='RO'))
      self.add(pr.RemoteVariable(name='Locked1',      description='Locked',         offset=0x00000034, bitSize=1,  bitOffset=16, base=pr.Bool, mode='RO'))      
      for i in range(0, 2):
         self.add(pr.RemoteVariable(name='IserdeseOutA'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000080+i*4, bitSize=16, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))
         self.add(pr.RemoteVariable(name='IserdeseOutB'+str(i),   description='IserdeseOut'+str(i),  offset=0x00000080+i*4, bitSize=16, bitOffset=16, base=pr.UInt, disp = '{:#x}', mode='RO'))

      self.add(pr.RemoteVariable(name='BERTRst',      description='Restart BERT',         offset=0x000000A0, bitSize=1,  bitOffset=1, base=pr.Bool, mode='RW'))      
      for i in range(0, 2):
         self.add(pr.RemoteVariable(name='BERTCounter'+str(i),   description='Counter value.'+str(i),  offset=0x000000A4+i*8, bitSize=44, bitOffset=0, base=pr.UInt,  disp = '{}', mode='RO'))

      self.add(AsicDeser14bDataRegisters(name='14bData_ser0',      offset=0x00000100, expand=False))
      self.add(AsicDeser14bDataRegisters(name='14bData_ser1',      offset=0x00000200, expand=False))
      #####################################
      # Create commands
      #####################################
      
      # A command has an associated function. The function can be a series of
      # python commands in a string. Function calls are executed in the command scope
      # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
      # A command can also be a call to a local function with local scope.
      # The command object and the arg are passed
      self.add(pr.LocalCommand(name='InitAdcDelay',description='Find and set best delay for the adc channels', function=self.fnSetFindAndSetDelays))
      

   def fnSetFindAndSetDelays(self,dev,cmd,arg):
       """Find and set Monitoring ADC delays"""
       parent = self.parent
       numDelayTaps = 512

       print("Executing delay test for cryo")

       self.testResult0 = np.zeros(numDelayTaps)
       self.testDelay0  = np.zeros(numDelayTaps)
       #check adc 0
       for delay in range (0, numDelayTaps):
           self.Delay0.set(delay)
           self.testDelay0[delay] = self.Delay0.get()
           self.Resync.set(True)
           self.Resync.set(False)
           time.sleep(1.0 / float(100))
           self.testResult0[delay] = ((self.IserdeseOutA0.get()==0x3407)or(self.IserdeseOutA0.get()==0xBF8)) 
       print("Test result adc 0:")
       print(self.testResult0*self.testDelay0)

       #check adc 1   
       self.testResult1 = np.zeros(numDelayTaps)
       self.testDelay1  = np.zeros(numDelayTaps)
       for delay in range (0, numDelayTaps):
           self.Delay1.set(delay)
           self.testDelay1[delay] = self.Delay1.get()
           self.Resync.set(True)
           self.Resync.set(False)
           time.sleep(1.0 / float(100))
           self.testResult1[delay] = ((self.IserdeseOutA1.get()==0x3407)or(self.IserdeseOutA1.get()==0xBF8)) 
       print("Test result adc 1:")     
       print(self.testResult1*self.testDelay1)
       
       self.resultArray0 =  np.zeros(numDelayTaps)
       self.resultArray1 =  np.zeros(numDelayTaps)
       for i in range(1, numDelayTaps):
           if (self.testResult0[i] != 0):
               self.resultArray0[i] = self.resultArray0[i-1] + self.testResult0[i]
           if (self.testResult1[i] != 0):
               self.resultArray1[i] = self.resultArray1[i-1] + self.testResult1[i]
       self.longestDelay0 = np.where(self.resultArray0==np.max(self.resultArray0))
       if len(self.longestDelay0[0])==1:
           self.sugDelay0 = int(self.longestDelay0[0]) - int(self.resultArray0[self.longestDelay0]/2)
       else:
           self.sugDelay0 = int(self.longestDelay0[0][0]) - int(self.resultArray0[self.longestDelay0[0][0]]/2)
       self.longestDelay1 = np.where(self.resultArray1==np.max(self.resultArray1))
       if len(self.longestDelay1[0])==1:
           self.sugDelay1 = int(self.longestDelay1[0]) - int(self.resultArray1[self.longestDelay1]/2)
       else:
           self.sugDelay1 = int(self.longestDelay1[0][0]) - int(self.resultArray1[self.longestDelay1[0][0]]/2)
       print("Suggested delay_0: " + str(self.sugDelay0))     
       print("Suggested delay_1: " + str(self.sugDelay1))     


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


class AsicDeser10bDataRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='10b data of 20 bit Deserializer Registers', **kwargs) 
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables  
      for i in range(0, 2):
         self.add(pr.RemoteVariable(name='tenbData_'+str(i),   description='Sample N_'+str(i),  offset=0x00000000+i*4, bitSize=10, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))

class AsicDeser14bDataRegisters(pr.Device):
   def __init__(self, **kwargs):
      super().__init__(description='10b data of 20 bit Deserializer Registers', **kwargs) 
      
      #############################################
      # Create block / variable combinations
      #############################################
      
      
      #Setup registers & variables  
      for i in range(0, 8):
         self.add(pr.RemoteVariable(name='14bData_'+str(i),   description='Sample N_'+str(i),  offset=0x00000000+i*4, bitSize=14, bitOffset=0, base=pr.UInt,  disp = '{:#x}', mode='RO'))

      
