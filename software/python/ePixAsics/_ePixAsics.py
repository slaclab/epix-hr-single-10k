#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Title      : PyRogue AXI Version Module
#-----------------------------------------------------------------------------
# File       : from pyrogue/devices/axi_version.py
# Author     : originally from Ryan Herbst, rherbst@slac.stanford.edu
#            : adapted by Dionisio Doering
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
import time as ti
import pyrogue as pr
import collections
import os
import numpy as np

usingPyQt5 = True

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore    import *
    from PyQt5.QtGui     import *
except ImportError:
    from PyQt4.QtCore    import *
    from PyQt4.QtGui     import *
    usingPyQt5 = False

#################################################################################################################
#
#  ASIC epix 10kT HR 
#
#################################################################################################################
class EpixHr10kTAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the ePix10kaAsic device"""
        super().__init__(description='EpixHrAdc Asic Configuration', **kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
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
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout',offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=False))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.RemoteVariable(name='shvc_DAC',      description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='fastPP_enable', description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserSync',    description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add((
            pr.RemoteVariable(name='Pll_RO_Reset',    description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Pll_Itune',       description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_KVCO',        description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1LSB',  description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1MSB',  description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW')))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 4 
        self.add((
            pr.RemoteVariable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='RefGenB',      description='Config5',  offset=0x00001005*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 6 
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef_DAC',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='VRefLow',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='trbit',     description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW')))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.RemoteVariable(name='TpsGr',       description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Balcony_clk', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='mTest',        description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2D_1_b', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='CompTH_DAC',    description='Config12', offset=0x0000100C*addrSize, bitSize=6, bitOffset=0, base=pr.UInt,  mode='RW')))
#        self.add((
#            pr.RemoteVariable(name='TS_mux',        description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=0, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='TS_clk_sel',    description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
#            pr.RemoteVariable(name='CompTH2_DAC',   description='Config12', offset=0x0000100C*addrSize, bitSize=3, bitOffset=3, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='Vtrim_b',       description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=6, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='Tsd_Tser',   description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Tps_DAC',    description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='PLL_RO_filter2',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PLL_RO_divider',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DigRO_disable',  description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelExec',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelCCKReg',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RO_rst_en',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SlvdsBit',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='FELmode',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='CompEnOn',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base=pr.UInt, mode='RO'))

        # CMD = 1, Addr = 22 
        self.add((
            pr.RemoteVariable(name='DCycle_DAC',    description='Config22', offset=0x00001016*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DCycle_en',     description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DCycle_bypass', description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='Debug_bit',    description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='OSRsel',       description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SecondOrder',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DHg',          description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RefGenC',      description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=5, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='dbus_del_sel', description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.RemoteVariable(name='SDclk_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='SDrst_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 25
        self.add((
            pr.RemoteVariable(name='Filter_DAC',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 26
        self.add((
            pr.RemoteVariable(name='CompEn',      description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pixel_CB',    description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW')))
        
        # CMD = 1, Addr = 27
        self.add((
            pr.RemoteVariable(name='rowCK2matrix_delay',   description='', offset=0x0000101b*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW')))

        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))
   
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=4, bitOffset=0,  function=pr.Command.touch, hidden=False))
 
        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.Variable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'),
        #    pr.Variable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))




        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.LocalCommand(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.LocalCommand(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.LocalCommand(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)
        if self._size == 0:
            self._size = 0xfffff

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (146, 192):
                    self._rawWrite(0x00000000*addrSize,0)
                    self._rawWrite(0x00008000*addrSize,0)
                    for x in range (0, 145):
                        for y in range (0, 192):
                            bankToWrite = int(y/48);
                            if (bankToWrite == 0):
                               colToWrite = 0x700 + y%48;
                            elif (bankToWrite == 1):
                               colToWrite = 0x680 + y%48;
                            elif (bankToWrite == 2):
                               colToWrite = 0x580 + y%48;
                            elif (bankToWrite == 3):
                               colToWrite = 0x380 + y%48;
                            else:
                               print('unexpected bank number')
                            self._rawWrite(0x00006011*addrSize, x)
                            self._rawWrite(0x00006013*addrSize, colToWrite) 
                            self._rawWrite(0x00005000*addrSize, (int(matrixCfg[x][y])))
                    self._rawWrite(0x00000000*addrSize,0)
                else:
                    print('csv file must be 192x146 pixels', matrixCfg.shape)
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        if self._size == 0:
            self._size = 0xfffff
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((146, 192),dtype='uint16')
                self._rawWrite(0x00000000*addrSize,0)
                self._rawWrite(0x00008000*addrSize,0)
                for x in range (0, 145):
                   for y in range (0, 192):
                      bankToWrite = int(y/48);
                      if (bankToWrite == 0):
                         colToWrite = 0x700 + y%48;
                      elif (bankToWrite == 1):
                         colToWrite = 0x680 + y%48;
                      elif (bankToWrite == 2):
                         colToWrite = 0x580 + y%48;
                      elif (bankToWrite == 3):
                         colToWrite = 0x380 + y%48;
                      else:
                         print('unexpected bank number')
                      self._rawWrite(0x00006011*addrSize, x)
                      self._rawWrite(0x00006013*addrSize, colToWrite)
                      readBack[x, y] = self._rawRead(0x00005000*addrSize)
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")             

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 48):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")          

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func



#################################################################################################################
#
#  ASIC epix 10kT V2 HR 
#
#################################################################################################################
class EpixHr10kTV2Asic(pr.Device):
    def __init__(self, **kwargs):
        """Create the ePixHR10kTAsic device"""
        super().__init__(**kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
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
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout',offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=False))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.RemoteVariable(name='shvc_DAC',      description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='fastPP_enable', description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserSync',    description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add((
            pr.RemoteVariable(name='Pll_RO_Reset',    description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Pll_Itune',       description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_KVCO',        description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1LSB',  description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pll_filter1MSB',  description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW')))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 4 
        self.add((
            pr.RemoteVariable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='RefGenB',      description='Config5',  offset=0x00001005*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 6 
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef_DAC',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='VRefLow',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='trbit',     description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt,  mode='RW'),
            pr.RemoteVariable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode='RW')))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.RemoteVariable(name='TpsGr',       description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Balcony_clk', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='mTest',        description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2D_1_b', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='CompTH_DAC',    description='Config12', offset=0x0000100C*addrSize, bitSize=6, bitOffset=0, base=pr.UInt,  mode='RW')))
#        self.add((
#            pr.RemoteVariable(name='TS_mux',        description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=0, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='TS_clk_sel',    description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
#            pr.RemoteVariable(name='CompTH2_DAC',   description='Config12', offset=0x0000100C*addrSize, bitSize=3, bitOffset=3, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='Vtrim_b',       description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=6, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='Tsd_Tser',   description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Tps_DAC',    description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            #pr.RemoteVariable(name='PLL_RO_filter1',   description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PLL_RO_filter2',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='PLL_RO_divider',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RSTreg',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelExec',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DelCCKReg',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RO_rst_en',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SlvdsBit',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='FELmode',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='CompEnOn',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base=pr.UInt, mode='RO'))

        # CMD = 1, Addr = 22 
        self.add((
            pr.RemoteVariable(name='DCycle_DAC',    description='Config22', offset=0x00001016*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='DCycle_en',     description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DCycle_bypass', description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='Debug_bit',    description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='OSRsel',       description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='SecondOrder',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='DHg',          description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode='RW'),
            pr.RemoteVariable(name='RefGenC',      description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=5, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='dbus_del_sel', description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode='RW')))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.RemoteVariable(name='SDclk_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='SDrst_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 25
        self.add((
            pr.RemoteVariable(name='Filter_DAC',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Rodis01',      description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 26
        self.add((
            pr.RemoteVariable(name='CompEn',      description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='Pixel_CB',    description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='rodis34',     description='', offset=0x0000101a*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode='RW')))
        
        # CMD = 1, Addr = 27
        self.add((
            pr.RemoteVariable(name='rowCK2matrix_delay',   description='', offset=0x0000101b*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='ro_mode',              description='', offset=0x0000101b*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode='RW'),
            pr.RemoteVariable(name='rodis5',               description='', offset=0x0000101b*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode='RW')))

        # CMD = 1, Addr = 28
        self.add((
            pr.RemoteVariable(name='pipoclk_delay',   description='', offset=0x0000101c*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode='RW')))

        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))
   
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteVariable(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=4, bitOffset=0, verify=False, hidden=False))
 
        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.Variable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'),
        #    pr.Variable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))




        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.LocalCommand(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.LocalCommand(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap, value='./pixelBitMaps/HR.csv'))
        
        self.add(
            pr.LocalCommand(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap, value='./pixelBitMaps/readBack.csv'))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)
        if self._size == 0:
            self._size = 0xfffff

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = [arg]
               print(arg)
            #else:
            #   self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
               if usingPyQt5:
                   self.filename = self.filename[0]
               if os.path.splitext(self.filename)[1] == '.csv':
                    matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                    if matrixCfg.shape == (146, 192):
                        self.CmdPrepForRead() #0000
                        self.PrepareMultiConfig() #8000
                        for x in range (0, 145):
                            for y in range (0, 192):
                                bankToWrite = int(y/48);
                                if (bankToWrite == 0):
                                    colToWrite = 0x700 + y%48;
                                elif (bankToWrite == 1):
                                    colToWrite = 0x680 + y%48;
                                elif (bankToWrite == 2):
                                    colToWrite = 0x580 + y%48;
                                elif (bankToWrite == 3):
                                    colToWrite = 0x380 + y%48;
                                else:
                                    print('unexpected bank number')
                                self.RowCounter.set(x) #6011
                                self.ColCounter.set(colToWrite) #6013
                                self.WritePixelData.set(int(matrixCfg[x][y])) #5000
                        self.CmdPrepForRead()

                    else:
                        print('csv file must be 192x146 pixels', matrixCfg.shape)
               else:
                   print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        if self._size == 0:
            self._size = 0xfffff
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = [arg]
            #else:
            #   self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((146, 192),dtype='uint16')
                self.CmdPrepForRead() #0000
                self.PrepareMultiConfig() #8000
                for x in range (0, 145):
                   for y in range (0, 192):
                      bankToWrite = int(y/48);
                      if (bankToWrite == 0):
                         colToWrite = 0x700 + y%48;
                      elif (bankToWrite == 1):
                         colToWrite = 0x680 + y%48;
                      elif (bankToWrite == 2):
                         colToWrite = 0x580 + y%48;
                      elif (bankToWrite == 3):
                         colToWrite = 0x380 + y%48;
                      else:
                         print('unexpected bank number')
                      self.RowCounter.set(x) #6011
                      self.ColCounter.set(colToWrite) #6013
                      readBack[x, y] = self.WritePixelData.get() #5000
                      if readBack[x, y] != 0:
                         print(readBack[x, y])
                print(self.filename)
                self.CmdPrepForRead() #0000
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")             

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 48):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(0)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")          

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func



#################################################################################################################
#
#  ASIC epix 10kT V3 HR 
#
#################################################################################################################
class EpixHr10kTV3Asic(pr.Device):
    def __init__(self, RegAccessMode='WO', **kwargs):
        """Create the ePixHR10kTAsic device"""
        super().__init__(**kwargs)


        #In order to easily compare GenDAQ address map with the ePix rogue address map 
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
    
        
        #Setup registers & variables
                
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout',offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=False))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.RemoteVariable(name='shvc_DAC',      description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='fastPP_enable', description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='PulserSync',    description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode=RegAccessMode)))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add((
            pr.RemoteVariable(name='Pll_RO_Reset',    description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='Pll_Itune',       description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Pll_KVCO',        description='Config2',  offset=0x00001002*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Pll_filter1LSB',  description='Config2',  offset=0x00001002*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Pll_filter1MSB',  description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode=RegAccessMode)))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.RemoteVariable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base=pr.Bool, mode=RegAccessMode)))

        # CMD = 1, Addr = 4 
        self.add((
            pr.RemoteVariable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode=RegAccessMode)))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.RemoteVariable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='RefGenB',      description='Config5',  offset=0x00001005*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 6 
        self.add((
            pr.RemoteVariable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode=RegAccessMode)))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.RemoteVariable(name='VRef_DAC',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='VRefLow',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.RemoteVariable(name='trbit',     description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base=pr.UInt,  mode=RegAccessMode),
            pr.RemoteVariable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base=pr.UInt,  mode=RegAccessMode)))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.RemoteVariable(name='TpsGr',       description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Balcony_clk', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode=RegAccessMode)))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.RemoteVariable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='mTest',        description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode=RegAccessMode)))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.RemoteVariable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='S2D_1_b', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.RemoteVariable(name='CompTH_DAC',    description='Config12', offset=0x0000100C*addrSize, bitSize=6, bitOffset=0, base=pr.UInt,  mode=RegAccessMode)))
#        self.add((
#            pr.RemoteVariable(name='TS_mux',        description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=0, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='TS_clk_sel',    description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode='RW'),
#            pr.RemoteVariable(name='CompTH2_DAC',   description='Config12', offset=0x0000100C*addrSize, bitSize=3, bitOffset=3, base=pr.UInt,  mode='RW'),
#            pr.RemoteVariable(name='Vtrim_b',       description='Config12', offset=0x0000100C*addrSize, bitSize=2, bitOffset=6, base=pr.UInt,  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.RemoteVariable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.RemoteVariable(name='Tsd_Tser',   description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Tps_DAC',    description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            #pr.RemoteVariable(name='PLL_RO_filter1',   description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='PLL_RO_filter2',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=2, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='PLL_RO_divider',   description='Config15', offset=0x0000100F*addrSize, bitSize=3, bitOffset=5, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.RemoteVariable(name='TestBe',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='RSTreg',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='DelExec',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='DelCCKReg',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='RO_rst_en',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='SlvdsBit',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='FELmode',        description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='CompEnOn',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode=RegAccessMode)))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.RemoteVariable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=8, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO'),
            pr.RemoteVariable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base=pr.UInt, mode='WO')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.RemoteVariable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base=pr.UInt, mode='RO'))

        # CMD = 1, Addr = 22 
        self.add((
            pr.RemoteVariable(name='DCycle_DAC',    description='Config22', offset=0x00001016*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='DCycle_en',     description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=6, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='DCycle_bypass', description='Config22', offset=0x00001016*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode=RegAccessMode)))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.RemoteVariable(name='Debug_bit',    description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='OSRsel',       description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=2, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='SecondOrder',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=3, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='DHg',          description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base=pr.Bool, mode=RegAccessMode),
            pr.RemoteVariable(name='RefGenC',      description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=5, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='dbus_del_sel', description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=7, base=pr.Bool, mode=RegAccessMode)))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.RemoteVariable(name='SDclk_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='SDrst_b',      description='', offset=0x00001018*addrSize, bitSize=4, bitOffset=4, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 25
        self.add((
            pr.RemoteVariable(name='Filter_DAC',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Rodis01',      description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 26
        self.add((
            pr.RemoteVariable(name='CompEn',      description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='Pixel_CB',    description='', offset=0x0000101a*addrSize, bitSize=3, bitOffset=3, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='rodis34',     description='', offset=0x0000101a*addrSize, bitSize=2, bitOffset=6, base=pr.UInt, mode=RegAccessMode)))
        
        # CMD = 1, Addr = 27
        self.add((
            pr.RemoteVariable(name='rowCK2matrix_delay',   description='', offset=0x0000101b*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='ro_mode',              description='', offset=0x0000101b*addrSize, bitSize=3, bitOffset=4, base=pr.UInt, mode=RegAccessMode),
            pr.RemoteVariable(name='rodis5',               description='', offset=0x0000101b*addrSize, bitSize=1, bitOffset=7, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 1, Addr = 28
        self.add((
            pr.RemoteVariable(name='pipoclk_delay',   description='', offset=0x0000101c*addrSize, bitSize=4, bitOffset=0, base=pr.UInt, mode=RegAccessMode)))

        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=4, bitOffset=0, function=pr.Command.touch, hidden=False)))
   
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteVariable(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=4, bitOffset=0, mode='RW', verify=False, hidden=False))
 
        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.Variable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'),
        #    pr.Variable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO')))
      
        # CMD = 8, Addr = X  : Prepare for row/column/matrix configuration
        self.add(
            pr.RemoteCommand(name='PrepareMultiConfig', description='PrepareMultiConfig', offset=0x00008000*addrSize, bitSize=32, bitOffset=0, function=pr.Command.touchZero, hidden=False))




        #####################################
        # Create commands
        #####################################

        # A command has an associated function. The function can be a series of
        # python commands in a string. Function calls are executed in the command scope
        # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
        # A command can also be a call to a local function with local scope.
        # The command object and the arg are passed

        self.add(
            pr.LocalCommand(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.LocalCommand(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap, value='./pixelBitMaps/HR.csv'))
        
        self.add(
            pr.LocalCommand(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap, value='./pixelBitMaps/readBack.csv'))

#    def enableChanged(self,value):
#        if value is True:
#            self.readBlocks(recurse=True, variable=None)
#            self.checkBlocks(recurse=True, variable=None)

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        addrSize = 4
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)
        if self._size == 0:
            self._size = 0xfffff

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = [arg]
               print(arg)
            #else:
            #   self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            # in PyQt5 QFileDialog returns a tuple
               if usingPyQt5:
                   self.filename = self.filename[0]
               if os.path.splitext(self.filename)[1] == '.csv':
                    matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                    print("ASIC V3")
                    if matrixCfg.shape == (146, 192):
                        self.CmdPrepForRead() #0000
                        self.PrepareMultiConfig() #8000
                        for x in range (0, 145):                            
                            for y in range (0, 192):
                                bankToWrite = int(y/48);
                                if (bankToWrite == 0):
                                    colToWrite = 0x700 + y%48;
                                elif (bankToWrite == 1):
                                    colToWrite = 0x680 + y%48;
                                elif (bankToWrite == 2):
                                    colToWrite = 0x580 + y%48;
                                elif (bankToWrite == 3):
                                    colToWrite = 0x380 + y%48;
                                else:
                                    print('unexpected bank number')
                                self.RowCounter.set(x) #6011
                                self.ColCounter.set(colToWrite) #6013
                                self.WritePixelData.set(int(matrixCfg[x][y])) #5000

                        self.CmdPrepForRead()

                    else:
                        print('csv file must be 192x146 pixels', matrixCfg.shape)
               else:
                   print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        addrSize = 4
        if self._size == 0:
            self._size = 0xfffff
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = [arg]
            #else:
            #   self.filename = QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if usingPyQt5:
               self.filename = self.filename[0]
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((146, 192),dtype='uint16')
                self.CmdPrepForRead() #0000
                self.PrepareMultiConfig() #8000
                for x in range (0, 145):
                   for y in range (0, 192):
                      bankToWrite = int(y/48);
                      if (bankToWrite == 0):
                         colToWrite = 0x700 + y%48;
                      elif (bankToWrite == 1):
                         colToWrite = 0x680 + y%48;
                      elif (bankToWrite == 2):
                         colToWrite = 0x580 + y%48;
                      elif (bankToWrite == 3):
                         colToWrite = 0x380 + y%48;
                      else:
                         print('unexpected bank number')
                      self.RowCounter.set(x) #6011
                      self.ColCounter.set(colToWrite) #6013
                      readBack[x, y] = self.WritePixelData.get() #5000
                      if readBack[x, y] != 0:
                         print(readBack[x, y])
                print(self.filename)
                self.CmdPrepForRead() #0000
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")             

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        #self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 48):
                self.PrepareMultiConfig()
                self.ColCounter.set(i)
                self.WriteColData.set(arg)
            self.CmdPrepForRead()
        else:
            print("Warning: ASIC enable is set to False!")          

    # standard way to report a command has been executed
    def reportCmd(self, dev,cmd,arg):
        """reportCmd command function"""
        "Enables to unify the console print out for all cmds"
        print("Command executed : ", cmd)

    @staticmethod   
    def frequencyConverter(self):
        def func(dev, var):         
            return '{:.3f} kHz'.format(1/(self.clkPeriod * self._count(var.dependencies)) * 1e-3)
        return func








