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
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
import numpy as np


#import epix.Epix100aAsic

class Epix100aAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the axiVersion device for ePix100aAsic"""
        super().__init__(description='Epix100a Asic Configuration', **kwargs)


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
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = 1  : Bits 2:0 - Pulser monostable bits
        #                      Bit  7   - Pulser sync bit
        self.add((pr.Variable(name='MonostPulser', description='MonoSt Pulser bits',   offset=0x00001001*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'),
                 pr.Command( name='PulserSync',   description='Pulse on SYNC signal', offset=0x00001001*addrSize, bitSize=1, bitOffset=7, function=pr.Command.touch)))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        #                    : Bit 0 = Test
        #                    : Bit 1 = Test
        self.add(pr.Variable(name='PixelDummy', description='Pixel dummy, write data', offset=0x00001002*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
        
        # TODO
        # check Variable("DummyMask") and Variable("DummyTest")
        # these variables don't seem to be needed in the rogue version of the software.

        # CMD = 1, Addr = 3  : Bits 9:0 = Pulser[9:0]
        #                    : Bit  10  = pbit
        #                    : Bit  11  = atest
        #                    : Bit  12  = test
        #                    : Bit  13  = sab_test
        #                    : Bit  14  = hrtest
        #                    : Bit  15  = PulserR
        self.add((
            pr.Variable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base='hex',  mode='RW'),
            pr.Variable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base='bool', mode='RW'),
            pr.Variable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base='bool', mode='RW'),
            pr.Variable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base='bool', mode='RW'),
            pr.Variable(name='sba_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base='bool', mode='RW'),
            pr.Variable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base='bool', mode='RW'),
            pr.Variable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base='bool', mode='RW')))

        # CMD = 1, Addr = 4  : Bits 3:0 = DM1[3:0]
        #                    : Bits 7:4 = DM2[3:0]
        
        self.add(
            pr.Variable(name='DigMon1', offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base='enum', mode='RW', enum={0:'Clk', 1:'Exec', 2:'RoRst', 3:'Ack',
            4:'IsEn', 5:'RoWClk', 6:'Addr0', 7:'Addr1', 8:'Addr2', 9:'Addr3', 10:'Addr4', 11:'Cmd0', 12:'Cmd1',
            13:'Cmd2', 14:'Cmd3', 15:'Config'}, description='Run rate of the system.'))         

        self.add(
            pr.Variable(name='DigMon2', offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base='enum', mode='RW', enum={0:'Clk', 1:'Exec', 2:'RoRst', 3:'Ack',
            4:'IsEn', 5:'RoWClk', 6:'Db0', 7:'Db1', 8:'Db2', 9:'Db3', 10:'Db4', 11:'Db5', 12:'Db6', 13:'Db7',
            14:'AddrMot', 15:'Config'}, description='Run rate of the system.'))         
 
        # CMD = 1, Addr = 5  : Bits 2:0 = Pulser DAC[2:0]
        #                      Bits 7:4 = TPS_GR[3:0]
        self.add((
            pr.Variable(name='PulserDac', description='Pulser Dac', offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='TpsGr',     description='',           offset=0x00001005*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))

        # CMD = 1, Addr = 6  : Bit  0   = DM1en
        #                    : Bit  1   = DM2en
        #                    : Bit  4   = SLVDSbit
        self.add((
            pr.Variable(name='Dm1En', description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='Dm2En', description='Digital Monitor 1 Enable', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'),
            pr.Variable(name='SLVDSbit', description='',                      offset=0x00001006*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.Variable(name='VRef',    description='Voltage Ref',                offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='VRefLow', description='Voltage Ref for Extra Rows', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base='hex', mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.Variable(name='TPS_tcomp',  description='', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='TPS_MUX',    description='', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base='enum',  mode='RW',
            enum={0:'in', 1:'fin', 2:'fo', 3:'abus', 4:'cdso3', 5:'bgr_2V', 
             6:'bgr_2vd', 7:'vc_comp', 8:'vcmi', 9:'Pix_Vref', 10:'VtestBE', 11:'Pix_Vctrl', 12:'testline', 
             13:'Unused13', 14:'Unused14', 15:'Unused15'}),
            pr.Variable(name='TPS_Monost', description='', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base='hex',  mode='RW')))

        # CMD = 1, Addr = 9  : Bit  3:0 = S2D0_GR[3:0]
        #                    : Bit  7:4 = S2D1_GR[3:0]
        self.add((
            pr.Variable(name='S2d0Gr', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d1Gr', description='', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.Variable(name='PpOcbS2d',     description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='Ocb',          description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base='hex',  mode='RW'),
            pr.Variable(name='Monost',       description='', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base='hex',  mode='RW'),
            pr.Variable(name='FastppEnable', description='', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.Variable(name='Preamp',  description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='PixelCb', description='', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base='hex', mode='RW'),
            pr.Variable(name='Vld1_b',  description='', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base='hex', mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.Variable(name='S2dTComp',  description='', offset=0x0000100C*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='FilterDac', description='', offset=0x0000100C*addrSize, bitSize=6, bitOffset=1, base='hex',  mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.Variable(name='TC',         description='', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d',        description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base='hex', mode='RW'),
            pr.Variable(name='S2dDacBias', description='', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base='hex', mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.Variable(name='TpsTcDac', description='', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='TpsDac',   description='', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.Variable(name='S2d0TcDac', description='', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d0Dac',   description='', offset=0x0000100F*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.Variable(name='TestBe',       description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='IsEn',         description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'),
            pr.Variable(name='DelExec',      description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base='bool', mode='RW'),
            pr.Variable(name='DelCckRef',    description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base='bool', mode='RW'),
            pr.Variable(name='ro_rst_exten', description='', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[9:0]
        # CMD = 1, Addr = 18 : Row stop  address[9:0]
        # CMD = 1, Addr = 19 : Col start  address[9:0]
        # CMD = 1, Addr = 20 : Col stop  address[9:0]
        self.add((
            pr.Variable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=10, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=10, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=10, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=10, bitOffset=0, base='hex', mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.Variable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

        # CMD = 1, Addr = 22 : Bit  3:0 = S2D2GR[3:0]
        #                    : Bit  7:4 = S2D3GR[5:0] #TODO check it this is not 3:0??
        self.add((
            pr.Variable(name='S2d2Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d3Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))

        # CMD = 1, Addr = 23 : Bit  1:0 = S2D1_tcDAC[1:0]
        #                    : Bit  7:2 = S2D1_DAC[5:0]
        # CMD = 1, Addr = 24 : Bit  1:0 = S2D2_tcDAC[1:0]
        #                    : Bit  7:2 = S2D2_DAC[5:0]  
        # CMD = 1, Addr = 25 : Bit  1:0 = S2D3_tcDAC[1:0]
        #                    : Bit  7:2 = S2D3_DAC[5:0]
        self.add((
            pr.Variable(name='S2d1TcDac', description='', offset=0x00001017*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d1Dac',   description='', offset=0x00001017*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW'),
            pr.Variable(name='S2d2TcDac', description='', offset=0x00001018*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d2Dac',   description='', offset=0x00001018*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW'),
            pr.Variable(name='S2d3TcDac', description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d3Dac',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))
        
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006011*addrSize, bitSize=9, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006013*addrSize, bitSize=11, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data  
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))
 
        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0,  function=pr.Command.touch, hidden=False))

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
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (354, 384):
                    self.CmdPrepForRead()
                    self.PrepareMultiConfig()
                    for x in range (0, 354):
                        for y in range (0, 384):
                            bankToWrite = int(y/96);
                            if (bankToWrite == 0):
                                colToWrite = 0x700 + y%96;
                            elif (bankToWrite == 1):
                                colToWrite = 0x680 + y%96;
                            elif (bankToWrite == 2):
                                colToWrite = 0x580 + y%96;
                            elif (bankToWrite == 3):
                                colToWrite = 0x380 + y%96;
                            else:
                                print('unexpected bank number')
                            self.RowCounter.set(x)
                            self.ColCounter.set(colToWrite)
                            self.WritePixelData.set(int(matrixCfg[x][y]))
                    self.CmdPrepForRead()
                else:
                    print('csv file must be 384x354 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):

            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
                self.filename = arg
            else:
                self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((354, 384),dtype='uint16')
                self.CmdPrepForRead()
                self.PrepareMultiConfig()
                for x in range (0, 354):
                    for y in range (0, 384):
                        bankToWrite = int(y/96);
                        if (bankToWrite == 0):
                            colToWrite = 0x700 + y%96;
                        elif (bankToWrite == 1):
                            colToWrite = 0x680 + y%96;
                        elif (bankToWrite == 2):
                            colToWrite = 0x580 + y%96;
                        elif (bankToWrite == 3):
                            colToWrite = 0x380 + y%96;
                        else:
                            print('unexpected bank number')
                        self.RowCounter.set(x)
                        self.ColCounter.set(colToWrite)
                        readBack[x, y] = self.WritePixelData.get()
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.ePix100aFPGA.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            for i in range (0, 96):
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


class Epix10kaAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create the ePix10kaAsic device"""
        super().__init__(description='Epix10ka Asic Configuration', **kwargs)


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
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = 1 
        # TODO: fix CompEn so it is one uint register
        self.add((
            pr.Variable(name='CompTH_DAC',   description='Config1',  offset=0x00001001*addrSize, bitSize=6, bitOffset=0, base='hex',  mode='RW'),
            pr.Variable(name='CompEn0',      description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=6, base='bool', mode='RW'),
            pr.Variable(name='CompEn1',      description='Config5',  offset=0x00001005*addrSize, bitSize=1, bitOffset=6, base='bool', mode='RW'),
            pr.Variable(name='CompEn2',      description='Config5',  offset=0x00001005*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW'),
            pr.Variable(name='PulserSync',   description='Config1',  offset=0x00001001*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW')))
        # CMD = 1, Addr = 2  : Pixel dummy, write data
        self.add(pr.Variable(name='PixelDummy', description='Pixel dummy, write data', offset=0x00001002*addrSize, bitSize=8, bitOffset=0, base='hex', mode='RW'))
        

        # CMD = 1, Addr = 3  
        self.add((
            pr.Variable(name='Pulser',   description='Config3', offset=0x00001003*addrSize, bitSize=10, bitOffset=0,  base='hex',  mode='RW'),
            pr.Variable(name='pbit',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=10, base='bool', mode='RW'),
            pr.Variable(name='atest',    description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=11, base='bool', mode='RW'),
            pr.Variable(name='test',     description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=12, base='bool', mode='RW'),
            pr.Variable(name='sab_test', description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=13, base='bool', mode='RW'),
            pr.Variable(name='hrtest',   description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=14, base='bool', mode='RW'),
            pr.Variable(name='PulserR',  description='Config3', offset=0x00001003*addrSize, bitSize=1,  bitOffset=15, base='bool', mode='RW')))

        # CMD = 1, Addr = 4 
        self.add((
            pr.Variable(name='DigMon1', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='DigMon2', description='Config4',offset=0x00001004*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))
 
        # CMD = 1, Addr = 5 
        self.add((
            pr.Variable(name='PulserDac',    description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='MonostPulser', description='Config5',  offset=0x00001005*addrSize, bitSize=3, bitOffset=3, base='hex', mode='RW')))

        # CMD = 1, Addr = 6 
        self.add((
            pr.Variable(name='Dm1En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='Dm2En',     description='Config6', offset=0x00001006*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'),
            pr.Variable(name='emph_bd',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=2, base='hex', mode='RW'),
            pr.Variable(name='emph_bc',   description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=5, base='hex', mode='RW')))
      
        # CMD = 1, Addr = 7  : Bit  5:0 = VREF[5:0]
        #                    : Bit  7:6 = VrefLow[1:0]
        self.add((
            pr.Variable(name='VRef',    description='Config7', offset=0x00001007*addrSize, bitSize=6, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='VRefLow', description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=6, base='hex', mode='RW')))

        # CMD = 1, Addr = 8  : Bit  0   = TPS_tcomp
        #                    : Bit  4:1 = TPS_MUX[3:0]
        #                    : Bit  7:5 = RO_Monost[2:0]
        self.add((
            pr.Variable(name='TpsTComp',  description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='TpsMux',    description='Config8', offset=0x00001008*addrSize, bitSize=4, bitOffset=1, base='hex',  mode='RW'),
            pr.Variable(name='RoMonost',  description='Config8', offset=0x00001008*addrSize, bitSize=3, bitOffset=5, base='hex',  mode='RW')))     

        # CMD = 1, Addr = 9 
        self.add((
            pr.Variable(name='TpsGr',  description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d0Gr', description='Config9', offset=0x00001009*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))
  
        # CMD = 1, Addr = 10 : Bit  0   = PP_OCB_S2D
        #                    : Bit  3:1 = OCB[2:0]
        #                    : Bit  6:4 = Monost[2:0]
        #                    : Bit  7   = fastpp_enable
        self.add((
            pr.Variable(name='PpOcbS2d',     description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='Ocb',          description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=1, base='hex',  mode='RW'),
            pr.Variable(name='Monost',       description='Config10', offset=0x0000100A*addrSize, bitSize=3, bitOffset=4, base='hex',  mode='RW'),
            pr.Variable(name='FastppEnable', description='Config10', offset=0x0000100A*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW')))
     
        # CMD = 1, Addr = 11 : Bit  2:0 = Preamp[2:0]
        #                    : Bit  5:3 = Pixel_CB[2:0]
        #                    : Bit  7:6 = Vld1_b[1:0]
        self.add((
            pr.Variable(name='Preamp',  description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='PixelCb', description='Config11', offset=0x0000100B*addrSize, bitSize=3, bitOffset=3, base='hex', mode='RW'),
            pr.Variable(name='Vld1_b',  description='Config11', offset=0x0000100B*addrSize, bitSize=2, bitOffset=6, base='hex', mode='RW')))

        # CMD = 1, Addr = 12 : Bit  0   = S2D_tcomp
        #                    : Bit  6:1 = Filter_Dac[5:0]
        self.add((
            pr.Variable(name='S2dTComp',           description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='FilterDac',          description='Config12', offset=0x0000100C*addrSize, bitSize=6, bitOffset=1, base='hex',  mode='RW'),
            pr.Variable(name='TestLVDTransmitter', description='Config12', offset=0x0000100C*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW')))

        # CMD = 1, Addr = 13 : Bit  1:0 = tc[1:0]
        #                    : Bit  4:2 = S2D[2:0]
        #                    : Bit  7:5 = S2D_DAC_BIAS[2:0]
        self.add((
            pr.Variable(name='TC',         description='Config13', offset=0x0000100D*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d',        description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=2, base='hex', mode='RW'),
            pr.Variable(name='S2dDacBias', description='Config13', offset=0x0000100D*addrSize, bitSize=3, bitOffset=5, base='hex', mode='RW')))

        # CMD = 1, Addr = 14 : Bit  1:0 = tps_tcDAC[1:0]
        #                    : Bit  7:2 = TPS_DAC[5:0]
        self.add((
            pr.Variable(name='TpsTcDac', description='Config14', offset=0x0000100E*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='TpsDac',   description='Config14', offset=0x0000100E*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))

        # CMD = 1, Addr = 15 : Bit  1:0 = S2D0_tcDAC[1:0]
        #                    : Bit  7:2 = S2D0_DAC[5:0]
        self.add((
            pr.Variable(name='S2d0TcDac', description='Config15', offset=0x0000100F*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d0Dac',   description='Config15', offset=0x0000100F*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))

        # CMD = 1, Addr = 16 : Bit  0   = test_BE
        #                    : Bit  1   = is_en
        #                    : Bit  2   = delEXEC
        #                    : Bit  3   = delCCkreg
        #                    : Bit  4   = ro_rst_exten
        self.add((
            pr.Variable(name='TestBe',       description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'),
            pr.Variable(name='IsEn',         description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'),
            pr.Variable(name='DelExec',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=2, base='bool', mode='RW'),
            pr.Variable(name='DelCckRef',    description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=3, base='bool', mode='RW'),
            pr.Variable(name='RO_rst_en',    description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW'),
            pr.Variable(name='SlvdsBit',     description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=5, base='bool', mode='RW'),
            pr.Variable(name='FELmode',      description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=6, base='bool', mode='RW'),
            pr.Variable(name='CompEnOn',     description='Config16', offset=0x00001010*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW')))

        # CMD = 1, Addr = 17 : Row start  address[8:0]
        # CMD = 1, Addr = 18 : Row stop  address[8:0]
        # CMD = 1, Addr = 19 : Col start  address[6:0]
        # CMD = 1, Addr = 20 : Col stop  address[6:0]
        self.add((
            pr.Variable(name='RowStartAddr', description='RowStartAddr', offset=0x00001011*addrSize, bitSize=9, bitOffset=0, base='hex', mode='WO'),
            pr.Variable(name='RowStopAddr',  description='RowStopAddr',  offset=0x00001012*addrSize, bitSize=9, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='ColStartAddr', description='ColStartAddr', offset=0x00001013*addrSize, bitSize=7, bitOffset=0, base='hex', mode='WO'),
            pr.Variable(name='ColStopAddr',  description='ColStopAddr',  offset=0x00001014*addrSize, bitSize=7, bitOffset=0, base='hex', mode='RW')))
   
        #  CMD = 1, Addr = 21 : Chip ID Read
        self.add(
            pr.Variable(name='ChipId', description='ChipId', offset=0x00001015*addrSize, bitSize=16, bitOffset=0, base='hex', mode='RO'))

        # CMD = 1, Addr = 22 
        self.add((
            pr.Variable(name='S2d1Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d2Gr', description='', offset=0x00001016*addrSize, bitSize=4, bitOffset=4, base='hex', mode='RW')))
        
        # CMD = 1, Addr = 23
        self.add((
            pr.Variable(name='S2d3Gr', description='', offset=0x00001017*addrSize, bitSize=4, bitOffset=0, base='hex',  mode='RW'),
            pr.Variable(name='trbit',  description='', offset=0x00001017*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW')))
        
        # CMD = 1, Addr = 24
        self.add((
            pr.Variable(name='S2d1TcDac', description='', offset=0x00001018*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d1Dac',   description='', offset=0x00001018*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))
        
        # CMD = 1, Addr = 25
        self.add((
            pr.Variable(name='S2d2TcDac', description='', offset=0x00001019*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d2Dac',   description='', offset=0x00001019*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))
        
        # CMD = 1, Addr = 26
        self.add((
            pr.Variable(name='S2d3TcDac', description='', offset=0x0000101A*addrSize, bitSize=2, bitOffset=0, base='hex', mode='RW'),
            pr.Variable(name='S2d3Dac',   description='', offset=0x0000101A*addrSize, bitSize=6, bitOffset=2, base='hex', mode='RW')))
        
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
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))

        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (178, 192):
                    self.CmdPrepForRead()
                    self.PrepareMultiConfig()
                    for x in range (0, 177):
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
                            self.RowCounter.set(x)
                            self.ColCounter.set(colToWrite)
                            self.WritePixelData.set(int(matrixCfg[x][y]))
                    self.CmdPrepForRead()
                else:
                    print('csv file must be 192x178 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      

    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((178, 192),dtype='uint16')
                self.CmdPrepForRead()
                self.PrepareMultiConfig()
                for x in range (0, 177):
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
                      self.RowCounter.set(x)
                      self.ColCounter.set(colToWrite)
                      readBack[x, y] = self.WritePixelData.get()
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")             

    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Epix10ka.EpixFpgaRegisters.AsicR0Mode.set(True)

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


class TixelAsic(pr.Device):
    def __init__(self, **kwargs):
        """Create registers for Tixel ASIC"""
        super().__init__(description='Tixel ASIC Configuration', **kwargs)
        
        addrSize = 4	
        
        # CMD = 0, Addr = 0  : Prepare for readout
        self.add(pr.RemoteCommand(name='CmdPrepForRead', description='ePix Prepare For Readout', 
                             offset=0x00000000*addrSize, bitSize=1, bitOffset=0, function=pr.Command.touchZero, hidden=True))
        
        # CMD = 1, Addr = xxx - Register set
        
        self.add(pr.Variable(name='RowStart',      description='RowStart',       offset=0x00001001*addrSize, bitSize=8,  bitOffset=0,  base='uint',  mode='WO'))
        self.add(pr.Variable(name='RowStop',       description='RowStop',        offset=0x00001002*addrSize, bitSize=8,  bitOffset=0,  base='uint',  mode='RW'))
        self.add(pr.Variable(name='ColumnStart',   description='ColumnStart',    offset=0x00001003*addrSize, bitSize=8,  bitOffset=0,  base='uint',  mode='WO'))
        self.add(pr.Variable(name='StartPixel',    description='StartPixel',     offset=0x00001004*addrSize, bitSize=16, bitOffset=0,  base='uint',  mode='RW'))
        self.add((
            pr.Variable(name='TpsDacGain',   description='Config5', offset=0x00001005*addrSize, bitSize=2, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='TpsDac',       description='Config5', offset=0x00001005*addrSize, bitSize=6, bitOffset=2,  base='uint', mode='RW'),
            pr.Variable(name='TpsGr',        description='Config5', offset=0x00001005*addrSize, bitSize=4, bitOffset=8,  base='uint', mode='RW'),
            pr.Variable(name='TpsMux',       description='Config5', offset=0x00001005*addrSize, bitSize=4, bitOffset=12, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='BiasTpsBuffer', description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='BiasTps',       description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=3,  base='uint', mode='RW'),
            pr.Variable(name='BiasTpsDac',    description='Config6', offset=0x00001006*addrSize, bitSize=3, bitOffset=6,  base='uint', mode='RW'),
            pr.Variable(name='DacComparator', description='Config6', offset=0x00001006*addrSize, bitSize=6, bitOffset=10, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='BiasComparator',     description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='Preamp',             description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=3,  base='uint', mode='RW'),
            pr.Variable(name='BiasDac',            description='Config7', offset=0x00001007*addrSize, bitSize=3, bitOffset=6,  base='uint', mode='RW'),
            pr.Variable(name='BgrCtrlDacTps',      description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=9,  base='uint', mode='RW'),
            pr.Variable(name='BgrCtrlDacComp',     description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=11, base='uint', mode='RW'),
            pr.Variable(name='DacComparatorGain',  description='Config7', offset=0x00001007*addrSize, bitSize=2, bitOffset=13, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='Ppbit',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=0,  base='bool', mode='RW'),
            pr.Variable(name='TestBe',          description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=1,  base='bool', mode='RW'),
            pr.Variable(name='DelExec',         description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=2,  base='bool', mode='RW'),
            pr.Variable(name='DelCCKreg',       description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=3,  base='bool', mode='RW'),
            pr.Variable(name='syncExten',       description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=4,  base='bool', mode='RW'),
            pr.Variable(name='syncRoleSel',     description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=5,  base='bool', mode='RW'),
            pr.Variable(name='hdrMode',         description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=6,  base='bool', mode='RW'),
            pr.Variable(name='acqRowlastEn',    description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=7,  base='bool', mode='RW'),
            pr.Variable(name='DM1en',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=8,  base='bool', mode='RW'),
            pr.Variable(name='DM2en',           description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=9,  base='bool', mode='RW'),
            pr.Variable(name='DigROdisable',    description='Config8', offset=0x00001008*addrSize, bitSize=1, bitOffset=10, base='bool', mode='RW')))
        self.add((
            pr.Variable(name='pllReset',        description='Config9', offset=0x00001009*addrSize, bitSize=1, bitOffset=0,  base='bool', mode='RW'),
            pr.Variable(name='pllItune',        description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=1,  base='uint', mode='RW'),
            pr.Variable(name='pllKvco',         description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=4,  base='uint', mode='RW'),
            pr.Variable(name='pllFilter1',      description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=7,  base='uint', mode='RW'),
            pr.Variable(name='pllFilter2',      description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=10, base='uint', mode='RW'),
            pr.Variable(name='pllOutDivider',   description='Config9', offset=0x00001009*addrSize, bitSize=3, bitOffset=13, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='pllROReset',      description='Config10', offset=0x0000100a*addrSize, bitSize=1, bitOffset=0,  base='bool', mode='RW'),
            pr.Variable(name='pllROItune',      description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=1,  base='uint', mode='RW'),
            pr.Variable(name='pllROKvco',       description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=4,  base='uint', mode='RW'),
            pr.Variable(name='pllROFilter1',    description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=7,  base='uint', mode='RW'),
            pr.Variable(name='pllROFilter2',    description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=10, base='uint', mode='RW'),
            pr.Variable(name='pllROOutDivider', description='Config10', offset=0x0000100a*addrSize, bitSize=3, bitOffset=13, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='dllGlobalCalib',     description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='dllCalibrationRang', description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=3,  base='uint', mode='RW'),
            pr.Variable(name='DllCpBias',          description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=6,  base='uint', mode='RW'),
            pr.Variable(name='DllAlockRen',        description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=9,  base='bool', mode='RW'),
            pr.Variable(name='DllReset',           description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=10, base='bool', mode='RW'),
            pr.Variable(name='DllDACvctrlEn',      description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=11, base='bool', mode='RW'),
            pr.Variable(name='DllBiasDisable',     description='Config11', offset=0x0000100b*addrSize, bitSize=1, bitOffset=12, base='bool', mode='RW'),
            pr.Variable(name='delayCellTestCalib', description='Config11', offset=0x0000100b*addrSize, bitSize=3, bitOffset=13, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='BiasVthCalibStepSize',  description='Config12', offset=0x0000100c*addrSize, bitSize=2, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='BiasVthCalibStepGlob',  description='Config12', offset=0x0000100c*addrSize, bitSize=3, bitOffset=2,  base='uint', mode='RW'),
            pr.Variable(name='BiasVthCalibTail',      description='Config12', offset=0x0000100c*addrSize, bitSize=3, bitOffset=5,  base='uint', mode='RW'),
            pr.Variable(name='GlobalCounterStart',    description='Config12', offset=0x0000100c*addrSize, bitSize=8, bitOffset=8,  base='uint', mode='RW')))
        self.add((
            pr.Variable(name='ROslvdsBit',   description='Config13', offset=0x0000100d*addrSize, bitSize=1, bitOffset=0,  base='bool', mode='RW'),
            pr.Variable(name='REFslvdsBit',  description='Config13', offset=0x0000100d*addrSize, bitSize=1, bitOffset=1,  base='bool', mode='RW'),
            pr.Variable(name='emphBc',       description='Config13', offset=0x0000100d*addrSize, bitSize=3, bitOffset=2,  base='uint', mode='RW'),
            pr.Variable(name='emphBd',       description='Config13', offset=0x0000100d*addrSize, bitSize=3, bitOffset=5,  base='uint', mode='RW'),
            pr.Variable(name='DM1Sel',       description='Config13', offset=0x0000100d*addrSize, bitSize=4, bitOffset=8,  base='uint', mode='RW'),
            pr.Variable(name='DM2Sel',       description='Config13', offset=0x0000100d*addrSize, bitSize=4, bitOffset=12, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='DacDllGain',      description='Config14', offset=0x0000100e*addrSize, bitSize=2, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='DacDll',          description='Config14', offset=0x0000100e*addrSize, bitSize=6, bitOffset=2,  base='uint', mode='RW'),
            pr.Variable(name='DacTestlineGain', description='Config14', offset=0x0000100e*addrSize, bitSize=2, bitOffset=8,  base='uint', mode='RW'),
            pr.Variable(name='DacTestline',     description='Config14', offset=0x0000100e*addrSize, bitSize=6, bitOffset=10, base='uint', mode='RW')))
        self.add((
            pr.Variable(name='DacpfaCompGain',  description='Config15', offset=0x0000100f*addrSize, bitSize=2, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='DacpfaComp',      description='Config15', offset=0x0000100f*addrSize, bitSize=6, bitOffset=2,  base='uint', mode='RW')))
        self.add((
            pr.Variable(name='LinearDecay',        description='Config16', offset=0x00001010*addrSize, bitSize=3, bitOffset=0,  base='uint', mode='RW'),
            pr.Variable(name='BGRctrlDACdll',      description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=3,  base='uint', mode='RW'),
            pr.Variable(name='BGRctrlDACtestine',  description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=5,  base='uint', mode='RW'),
            pr.Variable(name='BGRctrlDACpfaComp',  description='Config16', offset=0x00001010*addrSize, bitSize=2, bitOffset=7,  base='uint', mode='RW')))
         
        # CMD = 6, Addr = 17 : Row counter[8:0]
        self.add((
            pr.RemoteCommand(name='RowCounter', description='', offset=0x00006001*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False)))
        
        # CMD = 6, Addr = 19 : Bank select [3:0] & Col counter[6:0]
        self.add((
            pr.RemoteCommand(name='ColCounter', description='', offset=0x00006003*addrSize, bitSize=8, bitOffset=0, function=pr.Command.touch, hidden=False)))
            
        # CMD = 2, Addr = X  : Write Row with data
        self.add((
            pr.RemoteCommand(name='WriteRowData',    description='', offset=0x00002000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))

        # CMD = 3, Addr = X  : Write Column with data
        self.add(
            pr.RemoteCommand(name='WriteColData',    description='', offset=0x00003000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 4, Addr = X  : Write Matrix with data        
        self.add((    
            pr.RemoteCommand(name='WriteMatrixData', description='', offset=0x00004000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False)))   
        

        # CMD = 5, Addr = X  : Read/Write Pixel with data
        self.add(pr.RemoteCommand(name='WritePixelData',  description='WritePixelData',  offset=0x00005000*addrSize, bitSize=2, bitOffset=0, function=pr.Command.touch, hidden=False))

        # CMD = 7, Addr = X  : Prepare to write chip ID
        #self.add((
        #    pr.Variable(name='PrepareWriteChipIdA', description='PrepareWriteChipIdA', offset=0x00007000*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'),
        #    pr.Variable(name='PrepareWriteChipIdB', description='PrepareWriteChipIdB', offset=0x00007015*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW')))
      
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
            pr.Command(name='ClearMatrix',description='Clear configuration bits of all pixels', function=self.fnClearMatrix))
            
        self.add(
            pr.Command(name='SetPixelBitmap',description='Set pixel bitmap of the matrix', function=self.fnSetPixelBitmap))
        
        self.add(
            pr.Command(name='GetPixelBitmap',description='Get pixel bitmap of the matrix', function=self.fnGetPixelBitmap))

    def fnSetPixelBitmap(self, dev,cmd,arg):
        """SetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                matrixCfg = np.genfromtxt(self.filename, delimiter=',')
                if matrixCfg.shape == (48, 48):
                    self.CmdPrepForRead()
                    self.PrepareMultiConfig()
                    for x in range (0, 48):
                        for y in range (0, 48):
                            self.RowCounter.set(x)
                            self.ColCounter.set(y)
                            self.WritePixelData.set(int(matrixCfg[x][y]))
                    self.CmdPrepForRead()
                else:
                    print('csv file must be 48x48 pixels')
            else:
                print("Not csv file : ", self.filename)
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnGetPixelBitmap(self, dev,cmd,arg):
        """GetPixelBitmap command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            if len(arg) > 0:
               self.filename = arg
            else:
               self.filename = QtGui.QFileDialog.getOpenFileName(self.root.guiTop, 'Open File', '', 'csv file (*.csv);; Any (*.*)')
            if os.path.splitext(self.filename)[1] == '.csv':
                readBack = np.zeros((48,48),dtype='uint16')
                self.CmdPrepForRead()
                self.PrepareMultiConfig()
                for x in range (0, 48):
                   for y in range (0, 48):
                      self.RowCounter.set(x)
                      self.ColCounter.set(y)
                      readBack[x, y] = self.WritePixelData.get()
                np.savetxt(self.filename, readBack, fmt='%d', delimiter=',', newline='\n')
        else:
            print("Warning: ASIC enable is set to False!")      


    def fnClearMatrix(self, dev,cmd,arg):
        """ClearMatrix command function"""
        #set r0mode in order to have saci cmd to work properly on legacy firmware
        self.root.Tixel.TixelFpgaRegisters.AsicR0Mode.set(True)

        if (self.enable.get()):
            self.reportCmd(dev,cmd,arg)
            self.PrepareMultiConfig()
            self.WriteMatrixData.set(0)
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
