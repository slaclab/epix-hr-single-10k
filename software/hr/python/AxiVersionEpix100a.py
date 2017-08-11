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
# for genDAQ compatibility check software/deviceLib/AxiVersion.cpp
#-----------------------------------------------------------------------------
# This file is part of the rogue software platform. It is subject to 
# the license terms in the LICENSE.txt file found in the top-level directory 
# of this distribution and at: 
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
# No part of the rogue software platform, including this file, may be 
# copied, modified, propagated, or distributed except according to the terms 
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import pyrogue
import collections

def create(name='axiVersionEpix100a', offset=0, memBase=None, hidden=False, enabled=True):
    """Create the axiVersion device"""

    #In order to easely compare GedDAQ address map with the eprix rogue address map 
    #it is defined the addrSize variable
    addrSize = 4	

    # Creation. memBase is either the register bus server (srp, rce mapped memory, etc) or the device which
    # contains this object. In most cases the parent and memBase are the same but they can be 
    # different in more complex bus structures. They will also be different for the top most node.
    # The setMemBase call can be used to update the memBase for this Device. All sub-devices and local
    # blocks will be updated.
    dev = pyrogue.Device(name=name, memBase=memBase, offset=offset, hidden=hidden, size=0x1000,
                         description='AXI-Lite based common version block', enabled=enabled)

    #############################################
    # Create block / variable combinations
    #############################################

    # Next create a list of variables associated with this block.
    # base has two functions. If base = 'string' then the block is treated as a string (see BuildStamp)
    # otherwise the value is retrieved or set using:
    # setUInt(self.bitOffset,self.bitSize,value) or getUInt(self.bitOffset,self.bitSize)
    # otherwise base is used by a higher level interface (GUI, etc) to determine display mode
    # Allowed modes are RO, WO, RW or SL. SL indicates registers can be written but only
    # when executing commands (not accessed during writeAll and writeStale calls
    #Setup registers & variables
    dev.add(pyrogue.Variable(name='fpgaVersion', description='FPGA firmware version number',
                             offset=0x00*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))

    # Example of using setFunction and getFunction. setFunction and getFunctions are defined in the class
    # at the bottom. getFunction is defined as a series of python calls. When using the defined
    # function the scope is relative to the location of the function defintion. A pointer to the variable
    # and passed value are provided as args. See UserConstants below for an alernative method.
    dev.add(pyrogue.Variable(name='runTriggerEnable', description='Enable external run trigger',
                             offset=0x01*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='runTriggerDelay', description='Run trigger delay',
                             offset=0x02*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='daqTriggerEnable', description='Enable external run trigger',
                             offset=0x03*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
    
    dev.add(pyrogue.Variable(name='daqTriggerDelay', description='Run trigger delay',
                             offset=0x04*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='acqCount', description='Acquisition counter',
                             offset=0x05*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))

    dev.add(pyrogue.Variable(name='acqReset', description='Reset acquisition counter',
                             offset=0x06*addrSize, bitSize=32, bitOffset=0, base='hex', mode='WO'))

    dev.add(pyrogue.Variable(name='dacData', description='Sets analog DAC (MAX5443)',
                             offset=0x07*addrSize, bitSize=16, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='powerEnable', description='Analog power enable',
                             offset=0x08*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='frameCount', description='Frame counter',
                             offset=0x0B*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))

    dev.add(pyrogue.Variable(name='frameReset', description='Reset frame counter',
                             offset=0x0C*addrSize, bitSize=32, bitOffset=0, base='hex', mode='WO'))
    
    dev.add(pyrogue.Variable(name='asicMask', description='ASIC mask bits for the SACI access',
                             offset=0x0D*addrSize, bitSize=3, bitOffset=0, base='hex', mode='RW'))
    #Setup registers & variables
    dev.add(pyrogue.Variable(name='baseClock', description='FPGA base clock frequency',
                             offset=0x10*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))
    #Autotriggers
    dev.add(pyrogue.Variable(name='autoRunEnable', description='Enable auto run trigger',
                             offset=0x11*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='autoRunPeriod', description='Auto run trigger period',
                             offset=0x12*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='autoDaqEnable', description='Enable auto DAQ trigger',
                             offset=0x13*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='outPipelineDelay', description='Number of clock cycles to delay ASIC digital output bit',
                             offset=0x1F*addrSize, bitSize=8, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='acqToAsicR0Delay', description='Delay (in 10ns) between system acq and ASIC reset pulse',
                             offset=0x20*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='asicR0ToAsicAcq', description='Delay (in 10ns) between ASIC reset pulse and ASIC integration window',
                             offset=0x21*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='asicAcqWidth', description='Width (in 10ns) of ASIC acq signal',
                             offset=0x22*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='asicAcqLToPPmatL', description='Delay (in 10ns) between ASIC acq dropping and power pulse signal falling',
                             offset=0x23*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='asicRoClkHalfT', description='Width (in 10ns) of half of readout clock (10 = 5MHz)',
                             offset=0x24*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='adcReadsPerPixel', description='Number of ADC samples to record for each ASIC',
                             offset=0x25*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='adcClkHalfT', description='Width (in 8ns) of half clock period of ADC',
                             offset=0x26*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='totalPixelsToRead', description='Total numbers of pixels to be readout',
                             offset=0x27*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    #change this definition to expose individual bit
    #dev.add(pyrogue.Variable(name='asicPins', description='Manual ASIC pin controls',
    #                         offset=0x29*addrSize, bitSize=6, bitOffset=0, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='asicGR', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicAcq', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicRO', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=2, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPpmat', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=3, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPpbe', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicRoClk', description='Manual ASIC pin controls',
                             offset=0x29*addrSize, bitSize=1, bitOffset=5, base='bool', mode='RW'))


    #change this definition to expose individual bit
    #dev.add(pyrogue.Variable(name='asicPinControl', description='Manual ASIC pin controls',
    #                         offset=0x2A*addrSize, bitSize=11, bitOffset=0, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinGRControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinAcqControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinROControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=2, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinPpmatControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=3, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinPpbeControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=4, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='asicPinROClkControl', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=5, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='adcStreamMode', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=6, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='adcPatternEnable', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=7, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='ROMode', description='Manual ASIC pin controls',
                             offset=0x2A*addrSize, bitSize=1, bitOffset=8, base='bool', mode='RW'))



    dev.add(pyrogue.Variable(name='asicR0Width', description='Width of R0 low pulse',
                             offset=0x2B*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='digitalCardId0', description='Digital Card Serial Number (low 32 bits)',
                             offset=0x30*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='digitalCardId1', description='Digital Card Serial Number (high 32 bits)',
                             offset=0x31*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='analogCardId0', description='Analog Card Serial Number (low 32 bits)',
                             offset=0x32*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='analogCardId1', description='Analog Card Serial Number (high 32 bits)',
                             offset=0x33*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='asicPreAcqTime', description='Sum of time delays leading to the ASIC ACQ pulse',
                             offset=0x39*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))

    dev.add(pyrogue.Variable(name='asicPPmatToReadout', description='Delay (in 10ns) between Ppmat pulse and readout',
                             offset=0x3A*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='carrierCardId0', description='Carrier Card Serial Number (low 32 bits)',
                             offset=0x3B*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='carrierCardId1', description='Carrier Card Serial Number (high 32 bits)',
                             offset=0x3C*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='pgpTrigEn', description='Set to enable triggering over PGP. Disables the TTL trigger input',
                             offset=0x3D*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='monStreamEn', description='Set to enable monitor data stream over PGP',
                             offset=0x3E*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='tpsTiming', description='Delay TPS signal',
                             offset=0x40*addrSize, bitSize=16, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='tpsEdge', description='Sync TPS to rising or falling edge of Acq',
                             offset=0x40*addrSize, bitSize=1, bitOffset=16, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='swArmBit', description='Software arm bit',
                             offset=0x50*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='swTrgBit', description='Software trigger bit',
                             offset=0x51*addrSize, bitSize=1, bitOffset=0, base='bool', mode='WO'))

    dev.add(pyrogue.Variable(name='triggerADCEn', description='Trigger ADC enable',
                             offset=0x52*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))
    dev.add(pyrogue.Variable(name='triggerADCTh', description='Trigger ADC threshold',
                             offset=0x52*addrSize, bitSize=16, bitOffset=16, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='triggerADCMode', description='Trigger ADC mode',
                             offset=0x52*addrSize, bitSize=2, bitOffset=5, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='triggerADCChannel', description='Trigger ADC channel',
                             offset=0x52*addrSize, bitSize=4, bitOffset=2, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='triggerADCEdge', description='Trigger ADC edge',
                             offset=0x52*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RW'))

    dev.add(pyrogue.Variable(name='triggerHoldOff', description='Number of samples to wait after the trigger is armed',
                             offset=0x53*addrSize, bitSize=13, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='triggerTraceSkip', description='Number of samples to skip before recording starts',
                             offset=0x54*addrSize, bitSize=13, bitOffset=13, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='triggerTraceLength', description='Number of samples to record',
                             offset=0x54*addrSize, bitSize=13, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='inputChannelB', description='Select input channel B',
                             offset=0x55*addrSize, bitSize=5, bitOffset=5, base='hex', mode='RW'))
    dev.add(pyrogue.Variable(name='inputChannelA', description='Select input channel A',
                             offset=0x55*addrSize, bitSize=5, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='RequestStartup', description='Request startup sequence',
                             offset=0x80*addrSize, bitSize=1, bitOffset=0, base='bool', mode='WO'))
    dev.add(pyrogue.Variable(name='StartupDone', description='Startup sequence done',
                             offset=0x80*addrSize, bitSize=1, bitOffset=1, base='bool', mode='RO'))
    dev.add(pyrogue.Variable(name='StartupFail', description='Startup sequence failed',
                             offset=0x80*addrSize, bitSize=1, bitOffset=2, base='bool', mode='RO'))

    dev.add(pyrogue.Variable(name='requestConfDump', description='Request Conf. Dump',
                             offset=0x81*addrSize, bitSize=1, bitOffset=0, base='bool', mode='WO'))

    dev.add(pyrogue.Variable(name='adcPipelineDelayA0', description='Number of samples to delay ADC reads of the ASIC0 channels',
                             offset=0x90*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))
    
    dev.add(pyrogue.Variable(name='adcPipelineDelayA1', description='Number of samples to delay ADC reads of the ASIC1 channels',
                             offset=0x91*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='adcPipelineDelayA2', description='Number of samples to delay ADC reads of the ASIC2 channels',
                             offset=0x92*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='adcPipelineDelayA3', description='Number of samples to delay ADC reads of the ASIC3 channels',
                             offset=0x93*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))


    dev.add(pyrogue.Variable(name='EnvData00', description='Thermistor0 temperature',
                             offset=0x140*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData01', description='Thermistor1 temperature',
                             offset=0x141*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData02', description='Humidity',
                             offset=0x142*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData03', description='ASIC analog current',
                             offset=0x143*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData04', description='ASIC digital current',
                             offset=0x144*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData05', description='Guard ring current',
                             offset=0x145*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData06', description='Detector bias current',
                             offset=0x146*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData07', description='Analog raw input voltage',
                             offset=0x147*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

    dev.add(pyrogue.Variable(name='EnvData08', description='Digital raw input voltage',
                             offset=0x148*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))


    # Here we define MasterReset as mode 'SL' this will ensure it does not get written during
    # writeAll and writeStale commands
#    dev.add(pyrogue.Variable(name='masterResetVar', description='Optional User Reset',
#                             offset=0x06*addrSize, bitSize=1, bitOffset=0, base='bool', mode='SL', hidden=True))

#    dev.add(pyrogue.Variable(name='fpgaReloadVar', description='Optional reload the FPGA from the attached PROM',
#                             offset=0x07*addrSize, bitSize=1, bitOffset=0, base='bool', mode='SL', hidden=True))

#    dev.add(pyrogue.Variable(name='fpgaReloadAddress', description='Reload start address',
#                             offset=0x08*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RW'))

#    dev.add(pyrogue.Variable(name='counter', description='Free running counter', pollInterval=1,
#                             offset=0x09*addrSize, bitSize=32, bitOffset=0, base='hex', mode='RO'))

    # Bool is not used locally. Access will occur just as a uint or hex. The GUI will know how to display it.
#    dev.add(pyrogue.Variable(name='fpgaReloadHalt', description='Used to halt automatic reloads via AxiVersion',
#                             offset=0x0A*addrSize, bitSize=1, bitOffset=0, base='bool', mode='RW'))

#    dev.add(pyrogue.Variable(name='upTimeCnt', description='Number of seconds since reset', pollInterval=1,
#                             offset=0x2C, bitSize=32, bitOffset=0, base='uint', units="seconds", mode='RO'))

#    dev.add(pyrogue.Variable(name='deviceId', description='Device identification',
#                             offset=0x30, bitSize=32, bitOffset=0, base='hex', mode='RO'))

#    for i in range(0,64):
#
#        # Example of using setFunction and getFunction passed as strings. The scope is local to 
#        # the variable object with the passed value available as 'value' in the scope.
#        # The get function must set the 'value' variable as a result of the function.
#        dev.add(pyrogue.Variable(name='userConstant_%02i'%(i), description='Optional user input values',
#                                 offset=0x400+(i*4), bitSize=32, bitOffset=0, base='hex', mode='RW',
#                                 getFunction="""\
#                                             value = self._block.getUInt(self.bitOffset,self.bitSize)
#                                             """,
#                                 setFunction="""\
#                                             self._block.setUInt(self.bitOffset,self.bitSize,value)
#                                             """))

#    dev.add(pyrogue.Variable(name='UserConstants', description='User constants string',
#                             offset=0x100*addrSize, bitSize=256*8, bitOffset=0, base='string', mode='RO'))

#    dev.add(pyrogue.Variable(name='buildStamp', description='Firmware build string',
#                             offset=0x200*addrSize, bitSize=256*8, bitOffset=0, base='string', mode='RO'))

    #####################################
    # Create commands
    #####################################

    # A command has an associated function. The function can be a series of
    # python commands in a string. Function calls are executed in the command scope
    # the passed arg is available as 'arg'. Use 'dev' to get to device scope.
    dev.add(pyrogue.Command(name='masterReset',description='Master Reset',
                            function='dev.masterResetVar.post(1)'))
    
    # A command can also be a call to a local function with local scope.
    # The command object and the arg are passed
    dev.add(pyrogue.Command(name='fpgaReload',description='Reload FPGA',
                            function=cmdFpgaReload))

    dev.add(pyrogue.Command(name='counterReset',description='Counter Reset',
                            function='dev.counter.post(0)'))

    # Example printing the arg and showing a larger block. The indentation will be adjusted.
#    dev.add(pyrogue.Command(name='testCommand',description='Test Command',
#                            function="""\
#                                     print("Someone executed the %s command" % (self.name))
#                                     print("The passed arg was %s" % (arg))
#                                     print("My device is %s" % (dev.name))
#                                     """))

    # Alternative function for CPSW compatability
    # Pass a dictionary of numbered variable, value pairs to generate a CPSW sequence
    dev.add(pyrogue.Command(name='testCpsw',description='Test CPSW',
                            function=collections.OrderedDict({ 'masterResetVar': 1,
                                                               'usleep': 100,
                                                               'counter': 1 })))

    # Overwrite reset calls with local functions
    dev.setResetFunc(resetFunc)

    # Return the created device
    return dev


def cmdFpgaReload(dev,cmd,arg):
    """Example command function"""
    dev.fpgaReload.post(1)

def setVariableExample(dev,var,value):
    """Example set variable function"""
    var._block.setUInt(var.bitOffset,var.bitSize,value)

def getVariableExample(dev,var):
    """Example get variable function"""
    return(var._block.getUInt(var.bitOffset,var.bitSize))

def resetFunc(dev,rstType):
    """Application specific reset function"""
    if rstType == 'soft':
        dev.counter.set(0)
    elif rstType == 'hard':
        dev.masterResetVar.post(1)
    elif rstType == 'count':
        print('AxiVersion countReset')
        dev.counter.set(0)

